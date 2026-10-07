"""Optional Azure Functions v2 adapter. See docs/azure-deployment.md."""

import json
import logging
import os

import azure.functions as func
from azure.core import MatchConditions
from azure.core.exceptions import ResourceExistsError, ResourceModifiedError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

from transitpulse.cloud import ConcurrentPublishError, process_remote
from transitpulse.pipeline import QualityGateError

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


class AzureBlobStore:
    def __init__(self, container):
        self.container = container

    def read(self, key, limit):
        blob = self.container.get_blob_client(key)
        try:
            props = blob.get_blob_properties()
            if props.size > limit:
                raise ValueError(f'object exceeds the configured size limit: {key}')
            data = blob.download_blob(etag=props.etag, match_condition=MatchConditions.IfNotModified).readall()
            if len(data) > limit:
                raise ValueError('object exceeds the configured size limit')
            return data, props.etag
        except ResourceNotFoundError:
            return None
        except ResourceModifiedError as exc:
            raise ConcurrentPublishError('object changed during read; retry the batch') from exc

    def write_new(self, key, value):
        content_type = 'application/octet-stream'
        for extension, kind in {'.json': 'application/json', '.csv': 'text/csv', '.html': 'text/html', '.svg': 'image/svg+xml'}.items():
            if key.endswith(extension):
                content_type = kind
        self.container.get_blob_client(key).upload_blob(
            value, overwrite=False, content_settings=ContentSettings(content_type=content_type)
        )

    def compare_and_swap(self, key, value, expected_etag):
        blob = self.container.get_blob_client(key)
        try:
            if expected_etag is None:
                blob.upload_blob(value, overwrite=False, content_settings=ContentSettings(content_type='application/json'))
            else:
                blob.upload_blob(value, overwrite=True, etag=expected_etag,
                                 match_condition=MatchConditions.IfNotModified,
                                 content_settings=ContentSettings(content_type='application/json'))
        except (ResourceExistsError, ResourceModifiedError) as exc:
            raise ConcurrentPublishError('another run committed first; retry this batch') from exc


@app.route(route='process', methods=['POST'])
def process(req: func.HttpRequest) -> func.HttpResponse:
    try:
        if len(req.get_body()) > 4096:
            raise ValueError('request body exceeds 4 KiB')
        body = req.get_json()
        if not isinstance(body, dict) or set(body) != {'blob_name'}:
            raise ValueError('expected a JSON object containing only blob_name')
        # Credentials use the Function App managed identity in Azure, or az login locally.
        with DefaultAzureCredential() as credential:
            with BlobServiceClient(os.environ['TRANSITPULSE_STORAGE_URL'], credential=credential) as client:
                store = AzureBlobStore(client.get_container_client(os.environ.get('TRANSITPULSE_CONTAINER', 'transitpulse')))
                result = process_remote(store, body['blob_name'])
        return func.HttpResponse(json.dumps(result), status_code=200, mimetype='application/json')
    except ConcurrentPublishError as exc:
        return func.HttpResponse(json.dumps({'error': str(exc)}), status_code=409, mimetype='application/json')
    except QualityGateError as exc:
        return func.HttpResponse(json.dumps({'error': str(exc)}), status_code=422, mimetype='application/json')
    except (ValueError, FileNotFoundError) as exc:
        return func.HttpResponse(json.dumps({'error': str(exc)}), status_code=400, mimetype='application/json')
    except Exception:
        logging.exception('TransitPulse processing failed')
        return func.HttpResponse('{"error":"processing failed; inspect application logs"}', status_code=500, mimetype='application/json')

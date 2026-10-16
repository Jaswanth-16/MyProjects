import json
import urllib.request
import urllib.error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Provider redirects are not allowed")


class GroqClient:
    def __init__(self, key, model, *, endpoint="https://api.groq.com/openai/v1/chat/completions",
                 allow_local_test=False):
        if not key or not model:
            raise ValueError("Set GROQ_API_KEY and GROQ_MODEL explicitly")
        if endpoint != "https://api.groq.com/openai/v1/chat/completions":
            if not allow_local_test or not endpoint.startswith("http://127.0.0.1:"):
                raise ValueError("Unapproved provider endpoint")
        self.key, self.model, self.endpoint = key, model, endpoint

    def complete(self, messages):
        request = urllib.request.Request(self.endpoint, data=json.dumps({
            "model": self.model, "messages": messages, "temperature": 0,
            "max_completion_tokens": 700, "response_format": {"type": "json_object"}
        }).encode(), headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"})
        try:
            opener = urllib.request.build_opener(NoRedirect)
            with opener.open(request, timeout=25) as response:
                body = response.read(1000001)
            if len(body) > 1000000:
                raise ValueError("Provider response exceeds size limit")
            outer = json.loads(body)
            if outer["choices"][0].get("finish_reason") != "stop":
                raise ValueError("Incomplete model response")
            return json.loads(outer["choices"][0]["message"]["content"])
        except (urllib.error.URLError, OSError, KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            # Never expose headers, API keys, source text or the provider body.
            raise RuntimeError("Provider request failed") from None

import http.client,json,threading,unittest
from http.server import ThreadingHTTPServer
from loglens.server import handler_for
class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(0,'offline'))
        cls.port=cls.server.server_port;cls.server.RequestHandlerClass=handler_for(cls.port,'offline')
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,method,path,body=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        conn.request(method,path,body,headers or {});response=conn.getresponse();data=response.read();status=response.status;conn.close();return status,data
    def test_assets_and_options(self):
        for path in ['/','/app.js','/style.css','/api/options']:self.assertEqual(self.request('GET',path)[0],200)
        self.assertEqual(self.request('GET','/../data/runs.json')[0],404)
    def test_cross_origin_rejected(self):
        status,_=self.request('POST','/api/run','{}',{'Content-Type':'application/json','Origin':'https://evil.test'})
        self.assertEqual(status,403)
    def test_invalid_payload(self):
        headers={'Content-Type':'application/json','Origin':f'http://127.0.0.1:{self.port}'}
        self.assertEqual(self.request('POST','/api/run','{}',headers)[0],400)
    def test_real_offline_request(self):
        headers={'Content-Type':'application/json','Origin':f'http://127.0.0.1:{self.port}'}
        status,data=self.request('POST','/api/run',json.dumps({'log':'pipeline: demo\nSqlTimeout'}),headers)
        self.assertEqual(status,200);self.assertEqual(json.loads(data)['mode'],'offline')

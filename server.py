from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse, datetime, json, sqlite3, sys, threading, uuid, webbrowser
from guide import plan, clean
from engine import dilution, mixing, validate_experiment, predict, finishing, neutralization
from version import VERSION, APP_ID

RESOURCE_ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
DATA = APP_ROOT / 'data'
DB = DATA / 'lab.sqlite3'
PORT = 8873

def connect():
    DATA.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute('CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
    return c

def records():
    with connect() as c:
        return [json.loads(r[0]) for r in c.execute('SELECT payload FROM entries ORDER BY rowid DESC')]

def settings():
    with connect() as c:
        return {k: json.loads(v) for k,v in c.execute('SELECT key,value FROM settings')}

def backup(c, label):
    path = DATA / (label + '-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.sqlite3')
    dest = sqlite3.connect(path)
    try:c.backup(dest)
    finally:dest.close()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(RESOURCE_ROOT/'static'),**kw)
    def log_message(self,*args):pass
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()
    def sendj(self,data,status=200):
        b=json.dumps(data,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(b)))
        self.end_headers();self.wfile.write(b)
    def do_GET(self):
        if self.path=='/api/health':
            self.sendj(dict(app=APP_ID,version=VERSION));return
        if self.path=='/api/state':
            self.sendj(dict(records=records(),settings=settings(),version=VERSION));return
        if self.path=='/api/export':
            self.sendj(dict(schema=1,records=records(),settings=settings(),app_version=VERSION,exported=datetime.datetime.now().isoformat()));return
        if self.path.startswith('/api/'):
            self.sendj({'error':'接口不存在'},404);return
        super().do_GET()
    def do_POST(self):
        try:
            if self.headers.get('Host') not in [f'127.0.0.1:{PORT}',f'localhost:{PORT}']:
                raise ValueError('不接受外部Host')
            origin=self.headers.get('Origin','')
            if origin and origin not in [f'http://127.0.0.1:{PORT}',f'http://localhost:{PORT}']:
                raise ValueError('拒绝跨站请求')
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                raise ValueError('请使用JSON请求')
            size=int(self.headers.get('Content-Length',0))
            if size<1 or size>4000000:raise ValueError('请求大小不正确')
            d=json.loads(self.rfile.read(size))
            if not isinstance(d,dict):raise ValueError('请求应为JSON对象')
            if self.path=='/api/calculate':
                kind=d.pop('kind')
                functions={'dilution':dilution,'mixing':mixing,'finishing':finishing,'plan':plan,'clean':clean}
                if kind=='neutralization':result=neutralization(d,records())
                elif kind=='predict':result=predict(d,records())
                elif kind in functions:result=functions[kind](d)
                else:raise ValueError('未知计算')
                self.sendj(result);return
            if self.path=='/api/experiment':
                validate_experiment(d);d['id']=str(uuid.uuid4());d['created']=datetime.datetime.now().isoformat(timespec='seconds')
                with connect() as c:c.execute('INSERT INTO entries VALUES(?,?)',(d['id'],json.dumps(d,ensure_ascii=False)))
                self.sendj(d);return
            if self.path=='/api/delete':
                with connect() as c:
                    backup(c,'before-delete')
                    c.execute('DELETE FROM entries WHERE id=?',(d['id'],))
                self.sendj({'ok':True});return
            if self.path=='/api/settings':
                with connect() as c:
                    for k,v in d.items():c.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(k,json.dumps(v,ensure_ascii=False)))
                self.sendj({'ok':True});return
            if self.path=='/api/import':
                if d.get('schema')!=1:raise ValueError('不支持的备份格式')
                rs=d.get('records',[])
                if not isinstance(rs,list) or len(rs)>10000:raise ValueError('记录格式或数量不正确')
                for r in rs:validate_experiment(r)
                with connect() as c:
                    backup(c,'before-import')
                    for r in rs:
                        rid=r.get('id') or str(uuid.uuid4());r['id']=rid
                        c.execute('INSERT OR IGNORE INTO entries VALUES(?,?)',(rid,json.dumps(r,ensure_ascii=False)))
                    for k,v in d.get('settings',{}).items():c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',(k,json.dumps(v,ensure_ascii=False)))
                self.sendj({'ok':True,'count':len(rs)});return
            self.sendj({'error':'接口不存在'},404)
        except (ValueError,KeyError,TypeError,OverflowError) as e:self.sendj({'error':str(e)},400)
        except Exception:self.sendj({'error':'操作失败，请检查输入或数据目录权限'},500)

class LocalServer(ThreadingHTTPServer):
    allow_reuse_address=(sys.platform != 'win32')

def main():
    global DATA,DB,PORT
    parser=argparse.ArgumentParser(description='Probably Stolen local chemistry workbench')
    parser.add_argument('--version',action='version',version=VERSION)
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--port',type=int,default=8873)
    parser.add_argument('--data-dir',type=Path)
    args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error('port must be in 1..65535')
    PORT=args.port
    if args.data_dir:DATA=args.data_dir.resolve();DB=DATA/'lab.sqlite3'
    connect().close()
    url=f'http://127.0.0.1:{PORT}/'
    try:server=LocalServer(('127.0.0.1',PORT),Handler)
    except OSError:
        import urllib.request
        try:
            with urllib.request.urlopen(url+'api/health',timeout=2) as reply:health=json.load(reply)
            if health.get('app')==APP_ID and health.get('version')==VERSION:
                if not args.no_browser:webbrowser.open(url)
                print('工作台已经运行：'+url,flush=True);return 0
        except Exception:pass
        print(f'端口{PORT}被旧版或其他程序占用。请关闭旧的工作台窗口后重新启动；或用 --port 8874 指定其他端口。',flush=True)
        return 1
    if not args.no_browser:threading.Timer(.6,lambda:webbrowser.open(url)).start()
    print(f'深空化学工作台 v{VERSION}\n地址：{url}\n数据：{DATA}\n关闭此窗口即可停止服务。',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
    return 0

if __name__=='__main__':sys.exit(main())

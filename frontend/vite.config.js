import { defineConfig } from 'vite';
export default defineConfig({server:{proxy:{'/api':{
  target:'http://127.0.0.1:5001',
  rewrite:path=>path.replace(/^\/api/,''),
  configure(proxy){
    proxy.on('error',(_error,_request,response)=>{
      if (!response.headersSent && !response.destroyed && typeof response.writeHead==='function') {
        response.writeHead(503,{'Content-Type':'application/json'});
        response.end(JSON.stringify({error:'Cannot reach One Thing. Check that the backend is running, then try again.'}));
      }
    });
  },
}}}});

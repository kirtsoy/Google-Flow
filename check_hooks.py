import urllib.request, json, asyncio, websockets

async def check():
    r = urllib.request.urlopen('http://127.0.0.1:57764/json').read()
    targets = json.loads(r)
    tool_target = [t for t in targets if 'scf.usercontent.goog' in t.get('url', '')][-1]
    async with websockets.connect(tool_target['webSocketDebuggerUrl']) as ws:
        expr = """
        (() => {
            const el = document.querySelector('.min-h-full');
            const k = Object.keys(el).find(k => k.startsWith('__reactFiber'));
            let fiber = el[k];
            while (fiber.return) fiber = fiber.return;
            let targetNode = null;
            function search(node) {
                if (!node) return;
                if (node.memoizedState && typeof node.type === 'function' && node.type.name === 'App') {
                    targetNode = node; return;
                }
                let child = node.child;
                while (child) { search(child); if (targetNode) return; child = child.sibling; }
            }
            search(fiber);
            
            let h = targetNode.memoizedState;
            const res = [];
            for (let i = 0; i < 7; i++) {
                res.push({ i, val: h.memoizedState });
                h = h.next;
            }
            return res;
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        v = res.get('result', {}).get('result', {}).get('value', [])
        for item in v:
            val = item['val']
            print(f"Hook {item['i']}: {type(val)}", (len(val) if isinstance(val, (list, dict, str)) else val))
            if isinstance(val, list) and len(val) > 0:
                print("  Sample item:", val[0])

if __name__ == '__main__':
    asyncio.run(check())

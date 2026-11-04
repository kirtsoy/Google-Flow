import urllib.request, json, asyncio, websockets

async def get_app_code():
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
            return targetNode ? targetNode.type.toString() : '';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        s = res.get('result', {}).get('result', {}).get('value', '')
        with open('new_app_source.txt', 'w', encoding='utf-8') as f:
            f.write(s)
        print('Saved new App source, length:', len(s))

if __name__ == '__main__':
    asyncio.run(get_app_code())

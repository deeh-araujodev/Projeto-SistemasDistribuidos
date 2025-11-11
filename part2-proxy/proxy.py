
import zmq

ctx = zmq.Context()
xsub = ctx.socket(zmq.XSUB)
xpub = ctx.socket(zmq.XPUB)

xsub.bind("tcp://*:5557")  # servidor publica aqui
xpub.bind("tcp://*:5558")  # clientes/bots se inscrevem aqui

print("🔁 Proxy rodando (XSUB tcp://*:5557 ↔ XPUB tcp://*:5558)")
zmq.proxy(xsub, xpub)

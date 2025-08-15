# fitbox

## Prometheus

#creatr tunel:

```bash
   ssh -N -L 9090:127.0.0.1:9090 root@XXX.XXX.XX.XX


pytest -q tests/

mosquitto_pub -h 127.0.0.1 -p 1883 -t fitbox/ping   -m '{"device_id":"BAG02-M","ip":"192.168.1.47"}'
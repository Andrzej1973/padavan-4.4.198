# WR1200JS RC integration build evidence

GitHub run [37873926336](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37873926336) succeeded.
Built project revision: `98fe03cbae3764abb5f350c1d696b257967b87b4`.

- Image: `WR1200JS_4.4.198.9-100.trx`
- Size: 13098214 bytes
- SHA-256: `8cea539219b81719152fcfa7d77d3cdd4b7b592308eed7c6247a5b3ddebc96fb`

Downloaded source integration report confirms WR-only bridge object,
owned quiescence before radio stop, profile completion hook and DHCP hook.
It explicitly records `activation_integrated=false` and `runtime_verified=false`.
No startup currently sets either internal IoT activation guard. This image does
not establish a usable third Wi-Fi network or successful target runtime.

Separately, [ABI run 37876145618](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37876145618)
passed actual pinned native dnsmasq OFFER/ACK subnet/options and DNS transactions
for isolated IoT and LAN with generated firewall rules. Its retained JSON lists
four passed checks and records target runtime as unverified. This native host
fixture does not prove firmware service integration or actual radio behavior.

Remaining: complete interface/route inventory, production firewall integration,
serialized activation and rollback, service configuration staging, WebUI and
three-SSID isolation/reconnection acceptance on the router.

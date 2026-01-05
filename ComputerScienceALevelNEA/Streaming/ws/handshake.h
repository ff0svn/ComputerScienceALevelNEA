#ifndef HANDSHAKE_H
#define HANDSHAKE_H

int get_handshake_accept(char *wsKey, unsigned char **dest);
static char *strstricase(const char *haystack, const char *needle);
int get_handshake_response(char *hsrequest, char **hsresponse);

#define WS_KEY_LEN     24
#define WS_MS_LEN      36
#define WS_KEYMS_LEN   (WS_KEY_LEN + WS_MS_LEN)
#define MAGIC_STRING   "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

#define WS_HS_REQ      "Sec-WebSocket-Key"
#define WS_HS_ACCLEN   130
#define WS_HS_ACCEPT                       \
		"HTTP/1.1 101 Switching Protocols\r\n" \
		"Upgrade: websocket\r\n"               \
		"Connection: Upgrade\r\n"              \
		"Sec-WebSocket-Accept: "

#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h> /* (for random xid and secs) */
#include <sys/socket.h>
#include <netinet/in.h> /* (for struct sockaddr_in, IPPROTO_UDP) */
#include <arpa/inet.h> /* (for htons, ntohl, inet_addr, inet_ntoa or inet_ntop) */
#include <unistd.h> /* (for close) */
#include <sys/ioctl.h> /* (for ioctl) */
#include <errno.h>

/*
 * DHCP Packet Structure:
 */
#define DHCP_CHADDR_LEN 16
#define DHCP_SNAME_LEN  64
#define DHCP_FILE_LEN   128
#define DHCP_OPTIONS_BUF_LEN 312 // Max size of options field is 312 (576 - 240 - 24 for IP/UDP headers)
                                 // but typical options are much smaller. Start with a reasonable buffer.

// Operation codes
#define BOOTREQUEST 1
#define BOOTREPLY   2

// DHCP Message Type Option values (from RFC 2132)
#define DHCPDISCOVER 1
#define DHCPOFFER    2
#define DHCPREQUEST  3
#define DHCPDECLINE  4
#define DHCPACK      5
#define DHCPNAK      6
#define DHCPRELEASE  7
#define DHCPINFORM   8

// ... other types

// DHCP Options
#define DHCP_OPTION_PAD            0
#define DHCP_OPTION_SUBNET_MASK    1
#define DHCP_OPTION_ROUTER         3
#define DHCP_OPTION_DNS_SERVER     6
#define DHCP_OPTION_HOSTNAME       12
#define DHCP_OPTION_DOMAIN_NAME    15
#define DHCP_OPTION_IP_TTL         23
#define DHCP_OPTION_MTU            26
#define DHCP_OPTION_BROADCAST_ADDR 28
#define DHCP_OPTION_STATIC_ROUTE   33
#define DHCP_OPTION_TCP_TTL        37
#define DHCP_OPTION_NTP            42
#define DHCP_OPTION_NETBIOS_NAME_SRV 44
#define DHCP_OPTION_NETBIOS_NODE_TYPE 46
#define DHCP_OPTION_REQUESTED_IP   50
#define DHCP_OPTION_LEASE_TIME     51
#define DHCP_OPTION_MSG_TYPE       53
#define DHCP_OPTION_SERVER_ID      54
#define DHCP_OPTION_PARAM_REQ_LIST 55
#define DHCP_RENEWAL_TIME          58
#define DHCP_REBINDING_TIME        59
#define DHCP_OPTION_CLIENT_ID      61
#define DHCP_OPTION_LDAP           95
#define DHCP_OPTION_DISABLE_IPV4   108
#define DHCP_OPTION_CAPTIVE_PORTAL 114
#define DHCP_OPTION_DSL            119
#define DHCP_OPTION_CLASSLESS_STATIC_ROUTE 121
#define DHCP_OPTION_END            255

// Magic cookie validating DHCP options field
#define DHCP_MAGIC_COOKIE 0x63825363

typedef struct {
    uint8_t  op;            // Message op code / message type. 1 = BOOTREQUEST, 2 = BOOTREPLY
    uint8_t  htype;         // Hardware address type, see ARP section in "Assigned Numbers" RFC; e.g., '1' = 10mb ethernet.
    uint8_t  hlen;          // Hardware address length (e.g. '6' for 10mb ethernet).
    uint8_t  hops;          // Client sets to zero, optionally used by relay agents.
    uint32_t xid;           // Transaction ID, a random number.
    uint16_t secs;          // Seconds elapsed since client began address acquisition or renewal process.
    uint16_t flags;         // Flags (e.g. broadcast flag).
    uint32_t ciaddr;        // Client IP address; only filled in if client is in BOUND, RENEW or REBINDING state.
    uint32_t yiaddr;        // 'your' (client) IP address.
    uint32_t siaddr;        // Next server IP address (TFTP server).
    uint32_t giaddr;        // Relay agent IP address, else zero.
    uint8_t  chaddr[DHCP_CHADDR_LEN]; // Client hardware address.
    char     sname[DHCP_SNAME_LEN];   // Optional server host name, null terminated string.
    char     file[DHCP_FILE_LEN];     // Boot file name, null terminated string; "generic" name or null in DHCPDISCOVER.
    uint32_t magic_cookie;  // Magic cookie for DHCP options.
    uint8_t  options[DHCP_OPTIONS_BUF_LEN]; // Optional parameters field.
} dhcp_packet_t;

void dump_dhcp_packet(dhcp_packet_t *packet, int received_bytes) {
    printf("+---------------------------------------------------------------+\n");

    // Basic checks for a valid packet
    if ( (packet->op != BOOTREPLY) && (packet->op != BOOTREQUEST) ) {
        printf("Invalid message op code: %u\n", packet->op);
    } else {
        if (packet->op == BOOTREPLY) {
            printf("Message op code: BOOTREPLY (%u))\n", packet->op);
        } else {
            printf("Message op code: BOOTREQUEST (%u)\n", packet->op);
        }
    }
    if (ntohl(packet->magic_cookie) != DHCP_MAGIC_COOKIE) {
        printf("Received packet with invalid magic cookie.\n");
    } else {
        printf("Magic cookie: 0x%08X\n", ntohl(packet->magic_cookie));
    }
    // if (offer_packet.xid != discover_packet.xid) { // Compare in network byte order
    //     printf("Received packet with XID 0x%08X, expected 0x%08X. Ignoring.\n", ntohl(offer_packet.xid), ntohl(discover_packet.xid));
    //     continue;
    // }

    printf("Transaction ID (XID): 0x%08X\n", ntohl(packet->xid));

    // Offered IP Address ('yiaddr')
    struct in_addr yiaddr_struct;
    yiaddr_struct.s_addr = packet->yiaddr; // Already in network byte order for inet_ntoa
    printf("Offered IP Address (yiaddr): %s\n", inet_ntoa(yiaddr_struct));

    // DHCP Server IP Address ('siaddr')
    struct in_addr siaddr_struct;
    siaddr_struct.s_addr = packet->siaddr; // Already in network byte order for inet_ntoa
    printf("DHCP Server IP Address (siaddr): %s\n", inet_ntoa(siaddr_struct));

    // Client hardware address, i.e. MAC address
    printf("Client MAC address (chaddr): ");
    for (int i = 0; i < packet->hlen && i < DHCP_CHADDR_LEN; i++) {
        printf("%02X", packet->chaddr[i]);
        if (i < packet->hlen - 1 && i < DHCP_CHADDR_LEN - 1) printf(":");
    }
    printf("\n");    

    // Parse options
    unsigned char *opt_ptr = packet->options;
    unsigned char *end_options_ptr = (unsigned char *)packet + received_bytes; // End of received data

    while (opt_ptr < end_options_ptr && *opt_ptr != DHCP_OPTION_END) {
        if (*opt_ptr == DHCP_OPTION_PAD) {
            opt_ptr++;
            continue;
        }

        uint8_t opt_code = *opt_ptr++;
        uint8_t opt_len = 0;
        if (opt_ptr < end_options_ptr) { // Boundary check for length byte
            opt_len = *opt_ptr++;
        } else {
            fprintf(stderr, "Error: Option code %u found without length byte.\n", opt_code);
            break; // Corrupted options
        }


        if (opt_ptr + opt_len > end_options_ptr) { // Boundary check for option data
            fprintf(stderr, "Error: Option %u with length %u exceeds packet boundary.\n", opt_code, opt_len);
            break; // Corrupted options
        }


        switch (opt_code) {
            case DHCP_OPTION_MSG_TYPE:
                if (opt_len == 1) {
                    uint8_t msg_type_val = *opt_ptr;
                    printf("Option: DHCP Message Type (53) = ");
                    switch (msg_type_val) {
                        case DHCPDISCOVER:
                            printf("DHCPDISCOVER (1)\n");
                            break;
                        case DHCPOFFER:
                            printf("DHCPOFFER (2)\n");
                            break;
                        case DHCPREQUEST:
                            printf("DHCPREQUEST (3)\n");
                            break;
                        case DHCPDECLINE:
                            printf("DHCPDECLINE (4)\n");
                            break;
                        case DHCPACK:
                            printf("DHCPACK (5)\n");
                            break;
                        case DHCPNAK:
                            printf("DHCPNAK (6)\n");
                            break;
                        case DHCPRELEASE:
                            printf("DHCPRELEASE (7)\n");
                            break;
                        case DHCPINFORM:
                            printf("DHCPINFORM (8)\n");
                            break;
                        default:
                            printf("Unknown/Unexpected (%u)\n", msg_type_val);
                            break;
                    }
                }
                break;
            case DHCP_OPTION_SERVER_ID:
                if (opt_len == 4) {
                    struct in_addr server_id_addr;
                    memcpy(&server_id_addr.s_addr, opt_ptr, 4);
                    printf("Option: Server Identifier (54) = %s\n", inet_ntoa(server_id_addr));
                }
                break;
            case DHCP_OPTION_REQUESTED_IP:
                if (opt_len == 4) {
                    struct in_addr req_id_addr;
                    memcpy(&req_id_addr.s_addr, opt_ptr, 4);
                    printf("Option: Requested IP Address (50) = %s\n", inet_ntoa(req_id_addr));
                }
                break;
            case DHCP_OPTION_LEASE_TIME:
                if (opt_len == 4) {
                    uint32_t lease_time_net;
                    memcpy(&lease_time_net, opt_ptr, 4);
                    printf("Option: IP Address Lease Time (51) = %u seconds\n", ntohl(lease_time_net));
                }
                break;
            case DHCP_RENEWAL_TIME:
                if (opt_len == 4) {
                    uint32_t renewal_time_net;
                    memcpy(&renewal_time_net, opt_ptr, 4);
                    printf("Option: Renewal Time (58) = %u seconds\n", ntohl(renewal_time_net));
                }
                break;
            case DHCP_REBINDING_TIME:
                if (opt_len == 4) {
                    uint32_t rebinding_time_net;
                    memcpy(&rebinding_time_net, opt_ptr, 4);
                    printf("Option: Rebinding Time (59) = %u seconds\n", ntohl(rebinding_time_net));
                }
                break;
            case DHCP_OPTION_SUBNET_MASK:
                if (opt_len == 4) {
                    struct in_addr subnet_addr;
                    memcpy(&subnet_addr.s_addr, opt_ptr, 4);
                    printf("Option: Subnet Mask (1) = %s\n", inet_ntoa(subnet_addr));
                }
                break;
            case DHCP_OPTION_ROUTER:
                printf("Option: Router (3) = ");
                for (int i = 0; i < opt_len; i += 4) {
                    if (i + 4 <= opt_len) {
                        struct in_addr router_addr;
                        memcpy(&router_addr.s_addr, opt_ptr + i, 4);
                        printf("%s ", inet_ntoa(router_addr));
                    }
                }
                printf("\n");
                break;
            case DHCP_OPTION_DNS_SERVER:
                printf("Option: DNS Server (6) = ");
                for (int i = 0; i < opt_len; i += 4) {
                    if (i + 4 <= opt_len) {
                        struct in_addr dns_addr;
                        memcpy(&dns_addr.s_addr, opt_ptr + i, 4);
                        printf("%s ", inet_ntoa(dns_addr));
                    }
                }
                printf("\n");
                break;
            case DHCP_OPTION_BROADCAST_ADDR:
                printf("Option: Broadcast Address (28) = ");
                for (int i = 0; i < opt_len; i += 4) {
                    if (i + 4 <= opt_len) {
                        struct in_addr broadcast_addr;
                        memcpy(&broadcast_addr.s_addr, opt_ptr + i, 4);
                        printf("%s ", inet_ntoa(broadcast_addr));
                    }
                }
                printf("\n");
                break;
            case DHCP_OPTION_PARAM_REQ_LIST:
                printf("Option: Parameter Request List (55) =\n");
                for (int i = 0; i < opt_len; i++) {
                    switch (opt_ptr[i]) {
                        case DHCP_OPTION_SUBNET_MASK:
                            printf("\tSubnet Mask (1)\n");
                            break;
                        case DHCP_OPTION_ROUTER:
                            printf("\tRouter (3)\n");
                            break;
                        case DHCP_OPTION_DNS_SERVER:
                            printf("\tDNS Server (6)\n");
                            break;
                        case DHCP_OPTION_HOSTNAME:
                            printf("\tHostname (12)\n");
                            break;
                        case DHCP_OPTION_MTU:
                            printf("\tMTU (26)\n");
                            break;
                        case DHCP_OPTION_NTP:
                            printf("\tNTP (42)\n");
                            break;
                        case DHCP_OPTION_LEASE_TIME:
                            printf("\tLease Time (51)\n");
                            break;
                        case DHCP_OPTION_SERVER_ID:
                            printf("\tServer Id (54)\n");
                            break;
                        case DHCP_OPTION_DOMAIN_NAME:
                            printf("\tDomain Name (15)\n");
                            break;
                        case DHCP_OPTION_IP_TTL:
                            printf("\tIP TTL (23)\n");
                            break;
                        case DHCP_OPTION_BROADCAST_ADDR:
                            printf("\tBroadcast Address (28)\n");
                            break;
                        case DHCP_OPTION_STATIC_ROUTE:
                            printf("\tStatic Route (33)\n");
                            break;
                        case DHCP_OPTION_TCP_TTL:
                            printf("\tTCP TTL (37)\n");
                            break;
                        case DHCP_OPTION_NETBIOS_NAME_SRV:
                            printf("\tNETBIOS Name Server Id (44)\n");
                            break;
                        case DHCP_OPTION_NETBIOS_NODE_TYPE:
                            printf("\tNETBIOS Node Type (46)\n");
                            break;
                        case DHCP_OPTION_REQUESTED_IP:
                            printf("\tRequested IP Address (50)\n");
                            break;
                        case DHCP_RENEWAL_TIME:
                            printf("\tRenewal Time (58)\n");
                            break;
                        case DHCP_REBINDING_TIME:
                            printf("\tRebinding Time (59)\n");
                            break;
                        case DHCP_OPTION_CLIENT_ID:
                            printf("\tClient Id (61)\n");
                            break;
                        case DHCP_OPTION_LDAP:
                            printf("\tLDAP (95)\n");
                            break;
                        case DHCP_OPTION_DISABLE_IPV4:
                            printf("\tDisable IPv4 (108)\n");
                            break;
                        case DHCP_OPTION_CAPTIVE_PORTAL:
                            printf("\tCaptive Portal (114)\n");
                            break;
                        case DHCP_OPTION_DSL:
                            printf("\tDSL (119)\n");
                            break;
                        case DHCP_OPTION_CLASSLESS_STATIC_ROUTE:
                            printf("\tClassless Static Route (121)\n");
                            break;
                        default:
                            printf("\t%u\n", opt_ptr[i]);
                            break;
                    }
                }
                break;
            case DHCP_OPTION_CLIENT_ID:
                printf("Option: Client Identifier (61) = ");
                for (int i = 0; i < opt_len; i++) {
                    printf("%02X ", opt_ptr[i]);
                }
                printf("\n");
                break;
            // Add more cases for other options you requested or are interested in
            default:
                printf("Option: %u (Length: %u, Data: ", opt_code, opt_len);
                for (int i = 0; i < opt_len; i++) {
                    printf("%02X ", *(opt_ptr + i));
                }
                printf(")\n");
                break;
        }
        opt_ptr += opt_len;
    }
    printf("+---------------------------------------------------------------+\n");
}

int print_packet_info(dhcp_packet_t *packet, int received_bytes) {
    // Basic checks for a valid packet
    if ( (packet->op != BOOTREPLY) && (packet->op != BOOTREQUEST) ) {
        printf("Invalid message op code: %u\n", packet->op);
        return -1;
    }
    if (ntohl(packet->magic_cookie) != DHCP_MAGIC_COOKIE) {
        printf("Received packet with invalid magic cookie.\n");
        return -1;
    } 

    // Parse options
    unsigned char *opt_ptr = packet->options;
    unsigned char *end_options_ptr = (unsigned char *)packet + received_bytes; // End of received data

    uint8_t msg_type_val = 222; // Invalid code, means we didn't get a DHCP Message Type
    while (opt_ptr < end_options_ptr && *opt_ptr != DHCP_OPTION_END) {
        if (*opt_ptr == DHCP_OPTION_PAD) {
            opt_ptr++;
            continue;
        }

        uint8_t opt_code = *opt_ptr++;
        uint8_t opt_len = 0;
        if (opt_ptr < end_options_ptr) { // Boundary check for length byte
            opt_len = *opt_ptr++;
        } else {
            fprintf(stderr, "Error: Option code %u found without length byte.\n", opt_code);
            return -1; // Corrupted options
        }


        if (opt_ptr + opt_len > end_options_ptr) { // Boundary check for option data
            fprintf(stderr, "Error: Option %u with length %u exceeds packet boundary.\n", opt_code, opt_len);
            return -1; // Corrupted options
        }

        switch (opt_code) {
            case DHCP_OPTION_MSG_TYPE:
                if (opt_len == 1) {
                    msg_type_val = *opt_ptr;
                }
                break;
        }
        opt_ptr += opt_len;
    }
    printf("Received ");
    switch (msg_type_val) {
        case DHCPDISCOVER:
            printf("DHCPDISCOVER ");
            break;
        case DHCPOFFER:
            printf("DHCPOFFER ");
            break;
        case DHCPREQUEST:
            printf("DHCPREQUEST ");
            break;
        case DHCPDECLINE:
            printf("DHCPDECLINE ");
            break;
        case DHCPACK:
            printf("DHCPACK ");
            break;
        case DHCPNAK:
            printf("DHCPNAK ");
            break;
        case DHCPRELEASE:
            printf("DHCPRELEASE ");
            break;
        case DHCPINFORM:
            printf("DHCPINFORM ");
            break;
        default:
            printf("Unknown/Unexpected (%u) ", msg_type_val);
            break;
    }
    printf("packet with Transaction ID (XID): 0x%08X ", ntohl(packet->xid));
    printf("for MAC address: ");
    for (int i = 0; i < packet->hlen && i < DHCP_CHADDR_LEN; i++) {
        printf("%02X", packet->chaddr[i]);
        if (i < packet->hlen - 1 && i < DHCP_CHADDR_LEN - 1) printf(":");
    }
    printf(" offering IP %s ", inet_ntoa((struct in_addr){packet->yiaddr}));
    printf("from server %s\n", inet_ntoa((struct in_addr){packet->siaddr}));
    return 0;
}

void raw_dump_dhcp_packet(dhcp_packet_t *packet) {
    printf("+---------------------------------------------------------------+\n");
    printf("  op: %u (BOOTREQUEST: 1, BOOTREPLY: 2)\n", packet->op);
    printf("  htype: %u (Hardware Address Type)\n", packet->htype);
    printf("  hlen: %u (Hardware Address Length)\n", packet->hlen);
    printf("  hops: %u\n", packet->hops);
    printf("  xid: 0x%08X\n", ntohl(packet->xid));
    printf("  secs: %u\n", ntohs(packet->secs));
    printf("  flags: 0x%04X\n", ntohs(packet->flags));
    printf("  ciaddr: %s\n", inet_ntoa((struct in_addr){packet->ciaddr}));
    printf("  yiaddr: %s\n", inet_ntoa((struct in_addr){packet->yiaddr}));
    printf("  siaddr: %s\n", inet_ntoa((struct in_addr){packet->siaddr}));
    printf("  giaddr: %s\n", inet_ntoa((struct in_addr){packet->giaddr}));

    printf("  chaddr: ");
    for (int i = 0; i < packet->hlen && i < DHCP_CHADDR_LEN; i++) {
        printf("%02X", packet->chaddr[i]);
        if (i < packet->hlen - 1 && i < DHCP_CHADDR_LEN - 1) printf(":");
    }
    printf("\n");

    printf("  sname: %s\n", packet->sname);
    printf("  file: %s\n", packet->file);
    printf("  magic_cookie: 0x%08X (Expected: 0x63825363)\n", ntohl(packet->magic_cookie));

    printf("  options:\n");
    unsigned char *opt_ptr = packet->options;
    while (*opt_ptr != DHCP_OPTION_END && (size_t)(opt_ptr - (unsigned char *)packet) < DHCP_OPTIONS_BUF_LEN) {
        uint8_t opt_code = *opt_ptr++;
        uint8_t opt_len = 0;
        if (opt_ptr < (unsigned char *)packet + DHCP_OPTIONS_BUF_LEN) {
            opt_len = *opt_ptr++;
            printf("    Option: %u (Length: %u, Data: ", opt_code, opt_len);
            for (int i = 0; i < opt_len; i++) {
                printf("%02X ", *(opt_ptr + i));
            }
            printf(")\n");
        }    
        opt_ptr += opt_len;
    }
    printf("+---------------------------------------------------------------+\n");
}

uint32_t get_offered_ip(dhcp_packet_t *packet) {
    return packet->yiaddr;
}

uint32_t get_dhcp_server_ip(dhcp_packet_t *packet) {
    return packet->siaddr;
}

uint32_t get_x_id(dhcp_packet_t *packet) {
    return ntohl(packet->xid);
}

size_t create_discover_packet(dhcp_packet_t *packet, unsigned char *client_mac) {
    //
    // Construct DHCPDISCOVER Packet
    //
    packet->op = BOOTREQUEST;
    packet->htype = 1; // Ethernet
    packet->hlen = 6; // MAC address length
    packet->hops = 0;
    srand(time(NULL));
    packet->xid = htonl(rand()); // Random Transaction ID, network byte order
    packet->secs = htons(0); // Or time since boot attempt started
    packet->flags = htons(0x8000); // Broadcast flag (request broadcast reply)
    // ciaddr, yiaddr, siaddr, giaddr remain 0.
    memcpy(packet->chaddr, client_mac, 6);
    // sname and file can be left empty (zeroed out).
    packet->magic_cookie = htonl(DHCP_MAGIC_COOKIE);

    // Add DHCP Options
    unsigned char *options_ptr = packet->options;
    // Option 53: DHCP Message Type (DHCPDISCOVER)
    *options_ptr++ = DHCP_OPTION_MSG_TYPE;
    *options_ptr++ = 1; // Length
    *options_ptr++ = DHCPDISCOVER;

    // Option 55: Parameter Request List (example: subnet, router, dns, lease time, server id)
    *options_ptr++ = DHCP_OPTION_PARAM_REQ_LIST;
    *options_ptr++ = 5; // Length (for 5 options)
    *options_ptr++ = DHCP_OPTION_SUBNET_MASK;
    *options_ptr++ = DHCP_OPTION_ROUTER;
    *options_ptr++ = DHCP_OPTION_DNS_SERVER;
    *options_ptr++ = DHCP_OPTION_LEASE_TIME;
    *options_ptr++ = DHCP_OPTION_SERVER_ID;

    // Option 61: Client Identifier (Optional, but good practice. Type 1 + MAC)
    *options_ptr++ = DHCP_OPTION_CLIENT_ID;
    *options_ptr++ = 7; // Length: 1 (hw type) + 6 (mac)
    *options_ptr++ = 1; // Ethernet
    memcpy(options_ptr, client_mac, 6);
    options_ptr += 6;

    // End Option
    *options_ptr++ = DHCP_OPTION_END;

    // Return total packet size (up to the end of options written)
    return (size_t)(options_ptr - (unsigned char *)packet);
}

size_t create_request_packet(dhcp_packet_t *packet, unsigned char *client_mac, uint32_t xid, uint32_t *req_ip, uint32_t *dhcp_server) {
    //
    // Construct DHCPREQUEST Packet
    //
    packet->op = BOOTREQUEST;
    packet->htype = 1; // Ethernet
    packet->hlen = 6; // MAC address length
    packet->hops = 0;
    srand(time(NULL));
    packet->xid = htonl(xid); // Random Transaction ID, network byte order
    packet->secs = htons(0); // Or time since boot attempt started
    packet->flags = htons(0x8000); // Broadcast flag (request broadcast reply)
    memcpy(&packet->siaddr, dhcp_server, 4);
    // ciaddr, yiaddr, giaddr remain 0.
    memcpy(packet->chaddr, client_mac, 6);
    // sname and file can be left empty (zeroed out).
    packet->magic_cookie = htonl(DHCP_MAGIC_COOKIE);

    // Add DHCP Options
    unsigned char *options_ptr = packet->options;
    // Option 53: DHCP Message Type (DHCPDISCOVER)
    *options_ptr++ = DHCP_OPTION_MSG_TYPE;
    *options_ptr++ = 1; // Length
    *options_ptr++ = DHCPREQUEST;

    // Option 50: Requested IP Address 
    *options_ptr++ = DHCP_OPTION_REQUESTED_IP;
    *options_ptr++ = 4; // Length
    memcpy(options_ptr, req_ip, 4);
    options_ptr += 4;

    // Option 54: DHCP Server IP Address
    *options_ptr++ = DHCP_OPTION_SERVER_ID;
    *options_ptr++ = 4; // Length
    memcpy(options_ptr, dhcp_server, 4);
    options_ptr += 4;

    // End Option
    *options_ptr++ = DHCP_OPTION_END;

    // Return total packet size (up to the end of options written)
    return (size_t)(options_ptr - (unsigned char *)packet);
}

size_t create_release_packet(dhcp_packet_t *packet, unsigned char *client_mac, uint32_t xid, uint32_t *req_ip, uint32_t *dhcp_server) {
    //
    // Construct DHCPRELEASE Packet
    //
    packet->op = BOOTREQUEST;
    packet->htype = 1; // Ethernet
    packet->hlen = 6; // MAC address length
    packet->hops = 0;
    srand(time(NULL));
    packet->xid = htonl(xid); // Random Transaction ID, network byte order
    packet->secs = htons(0); // Or time since boot attempt started
    packet->flags = htons(0x8000); // Broadcast flag (request broadcast reply)
    memcpy(&packet->siaddr, dhcp_server, 4);
    // ciaddr, yiaddr, giaddr remain 0.
    memcpy(packet->chaddr, client_mac, 6);
    // sname and file can be left empty (zeroed out).
    packet->magic_cookie = htonl(DHCP_MAGIC_COOKIE);

    // Add DHCP Options
    unsigned char *options_ptr = packet->options;
    // Option 53: DHCP Message Type (DHCPDISCOVER)
    *options_ptr++ = DHCP_OPTION_MSG_TYPE;
    *options_ptr++ = 1; // Length
    *options_ptr++ = DHCPRELEASE;

    // Option 50: Requested IP Address 
    *options_ptr++ = DHCP_OPTION_REQUESTED_IP;
    *options_ptr++ = 4; // Length
    memcpy(options_ptr, req_ip, 4);
    options_ptr += 4;

    // Option 54: DHCP Server IP Address
    *options_ptr++ = DHCP_OPTION_SERVER_ID;
    *options_ptr++ = 4; // Length
    memcpy(options_ptr, dhcp_server, 4);
    options_ptr += 4;

    // End Option
    *options_ptr++ = DHCP_OPTION_END;

    // Return total packet size (up to the end of options written)
    return (size_t)(options_ptr - (unsigned char *)packet);
}

int monitor_dhcp_on_lan(int verbose, int use_raw) {

    // DHCP messages from a client to a server are sent to the 'DHCP server' port (67), and DHCP
    // messages from a server to a client are sent to the 'DHCP client' port (68).
    //
    // Port 68 
    //
    int sockfd68;
    if ((sockfd68 = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }

    int broadcast_enable = 1;
    if (setsockopt(sockfd68, SOL_SOCKET, SO_BROADCAST, &broadcast_enable, sizeof(broadcast_enable)) < 0) {
        perror("setsockopt SO_BROADCAST failed");
        close(sockfd68);
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in addr68;
    socklen_t addr68_len = sizeof(addr68);
    memset(&addr68, 0, sizeof(addr68));
    addr68.sin_family = AF_INET;
    addr68.sin_port = htons(68); // DHCP client port
    addr68.sin_addr.s_addr = INADDR_ANY; // Listen on all interfaces

    if (bind(sockfd68, (struct sockaddr *)&addr68, sizeof(addr68)) < 0) {
        perror("bind port 68 failed");
        close(sockfd68);
        exit(EXIT_FAILURE);
    }


    //
    // Port 67
    //
    int sockfd67;
    if ((sockfd67 = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in addr67;
    memset(&addr67, 0, sizeof(addr67));
    addr67.sin_family = AF_INET;
    addr67.sin_port = htons(67); // DHCP server port
    addr67.sin_addr.s_addr = INADDR_ANY;

    if (bind(sockfd67, (struct sockaddr *)&addr67, sizeof(addr67)) < 0) {
        perror("bind on port 67 failed");
        close(sockfd67);
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in source_addr;
    socklen_t source_addr_len = sizeof(source_addr);
    int received_bytes;
    dhcp_packet_t packet67;
    dhcp_packet_t packet68;

    // printf("Waiting for traffic...\n");
    // while (1) {
    //     memset(&offer_packet, 0, sizeof(offer_packet)); // Clear buffer for next packet
    //     received_bytes = recvfrom(sockfd68, &offer_packet, sizeof(offer_packet), 0,
    //                             (struct sockaddr *)&source_addr, &source_addr_len);

    //     if (received_bytes < 0) {
    //         continue;
    //     }
    //     if(verbose) {
    //         if(use_raw)
    //             raw_dump_dhcp_packet(&offer_packet);
    //         else
    //             dump_dhcp_packet(&offer_packet, received_bytes);
    //     } 
    //     print_packet_info(&offer_packet, received_bytes);
    // } 

    fd_set read_fds;
    int max_fd = (sockfd67 > sockfd68) ? sockfd67 : sockfd68;
    
    printf("Waiting for traffic...\n");
    while (1) {
        FD_ZERO(&read_fds);
        FD_SET(sockfd67, &read_fds);
        FD_SET(sockfd68, &read_fds);
    
        int activity = select(max_fd + 1, &read_fds, NULL, NULL, NULL);
        if (activity < 0) {
            perror("select error");
            continue;
        }
    
        if (FD_ISSET(sockfd67, &read_fds) || FD_ISSET(sockfd68, &read_fds)) {
            struct sockaddr_in source_addr;
            socklen_t source_addr_len = sizeof(source_addr);
            memset(&packet67, 0, sizeof(packet67));
            memset(&packet68, 0, sizeof(packet68));
    
            if (FD_ISSET(sockfd68, &read_fds))
                printf("FD_ISSET(sockfd68, &read_fds)\n");

            if (FD_ISSET(sockfd67, &read_fds))
                printf("FD_ISSET(sockfd67, &read_fds)\n");

            int received_bytes;
            if (FD_ISSET(sockfd68, &read_fds)) {
                received_bytes = recvfrom(sockfd68, &packet68, sizeof(packet68), 0,
                                          (struct sockaddr *)&source_addr, &source_addr_len);
printf("Bytes received from sockfd68: %d\n", received_bytes);

                if (verbose) {
                    if (use_raw)
                        raw_dump_dhcp_packet(&packet68);
                    else
                        dump_dhcp_packet(&packet68, received_bytes);
                }
                print_packet_info(&packet68, received_bytes);           
            } 
            
            if (FD_ISSET(sockfd67, &read_fds)) {
                received_bytes = recvfrom(sockfd67, &packet67, sizeof(packet67), 0,
                                          (struct sockaddr *)&source_addr, &source_addr_len);
printf("Bytes received from sockfd67: %d\n", received_bytes);

                if (verbose) {
                    if (use_raw)
                        raw_dump_dhcp_packet(&packet67);
                    else
                        dump_dhcp_packet(&packet67, received_bytes);
                }
                print_packet_info(&packet67, received_bytes);           
            }             
        }
    }
    
    exit(0);
}

int main(int argc, char *argv[]) {
    int use_raw = 0;
    int verbose = 0;
    int full_dora = 0;
    int monitor_only = 0;
    
    if (argc > 1) { 
        for (int i = 1; i < argc; i++) {
            if (strcmp(argv[i], "-r") == 0) {
                full_dora = 1;
            }
            if (strcmp(argv[i], "-v") == 0) {
                verbose = 1;
            }
            if (strcmp(argv[i], "-vv") == 0) {
                verbose = 1;
                use_raw = 1;
            }
            if (strcmp(argv[i], "-m") == 0) {
                monitor_only = 1;
            }
        }
    }

    //
    // Monitor mode
    //
    if(monitor_only) {
        monitor_dhcp_on_lan(verbose, use_raw);
        exit(0);
    }


    dhcp_packet_t discover_packet;
    memset(&discover_packet, 0, sizeof(discover_packet));

    // Example: Hardcoded MAC (replace with actual or dynamic retrieval later)
    // 00:0C:29:12:34:56
    unsigned char client_mac[6] = {0x00, 0x0C, 0x29, 0x12, 0x34, 0x56};

    //
    // Create and Configure UDP Socket
    //
    int sockfd;
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }

    int broadcast_enable = 1;
    if (setsockopt(sockfd, SOL_SOCKET, SO_BROADCAST, &broadcast_enable, sizeof(broadcast_enable)) < 0) {
        perror("setsockopt SO_BROADCAST failed");
        close(sockfd);
        exit(EXIT_FAILURE);
    }
    
    //
    // Prepare broadcast receive address structure (port 67)
    //
    struct sockaddr_in server_addr_broadcast;
    memset(&server_addr_broadcast, 0, sizeof(server_addr_broadcast));
    server_addr_broadcast.sin_family = AF_INET;
    server_addr_broadcast.sin_port = htons(67); // DHCP server port
    server_addr_broadcast.sin_addr.s_addr = inet_addr("255.255.255.255");
    // Or: server_addr_broadcast.sin_addr.s_addr = htonl(INADDR_BROADCAST);

    // Set a receive timeout
    struct timeval tv;
    tv.tv_sec = 5; // 5 seconds timeout
    tv.tv_usec = 0;
    if (setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv) < 0) {
        perror("setsockopt SO_RCVTIMEO failed");
        // Non-fatal, but good to know
    }
    
    //
    // Prepare client address structure (to bind to client port 68)
    //
    struct sockaddr_in client_addr;
    memset(&client_addr, 0, sizeof(client_addr));
    client_addr.sin_family = AF_INET;
    client_addr.sin_port = htons(68); // DHCP client port
    client_addr.sin_addr.s_addr = INADDR_ANY; // Listen on all interfaces

    if (bind(sockfd, (struct sockaddr *)&client_addr, sizeof(client_addr)) < 0) {
        perror("bind failed");
        close(sockfd);
        exit(EXIT_FAILURE);
    }
    
    size_t packet_size = create_discover_packet(&discover_packet, client_mac);
    if(verbose) {
        if(use_raw)
            raw_dump_dhcp_packet(&discover_packet);
        else
            dump_dhcp_packet(&discover_packet, sizeof(discover_packet));
    }

    //
    // Send the DHCPDISCOVER
    //
    printf("Sending DHCPDISCOVER (XID: 0x%08X) to 255.255.255.255...\n", ntohl(discover_packet.xid));
    if (sendto(sockfd, &discover_packet, packet_size, 0,
            (struct sockaddr *)&server_addr_broadcast, sizeof(server_addr_broadcast)) < 0) {
        perror("sendto failed");
        close(sockfd);
        exit(EXIT_FAILURE);
    }

    /* Receive and Parse DHCPOFFER Replies */

    dhcp_packet_t offer_packet;
    dhcp_packet_t last_offer_packet;
    struct sockaddr_in source_addr;
    socklen_t source_addr_len = sizeof(source_addr);
    int received_bytes;

    printf("Waiting for DHCPOFFER(s)...\n");
    while (1) { // Loop to catch multiple offers or until timeout
        memset(&offer_packet, 0, sizeof(offer_packet)); // Clear buffer for next packet
        received_bytes = recvfrom(sockfd, &offer_packet, sizeof(offer_packet), 0,
                                (struct sockaddr *)&source_addr, &source_addr_len);

        if (received_bytes < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) { // EAGAIN/EWOULDBLOCK for non-blocking timeout
                printf("Receive timeout. No more offers.\n");
            } else {
                perror("recvfrom failed");
            }
            break; // Exit loop on error or timeout
        }
        if(verbose) {
            if(use_raw)
                raw_dump_dhcp_packet(&offer_packet);
            else
                dump_dhcp_packet(&offer_packet, received_bytes);
        } 
        print_packet_info(&offer_packet, received_bytes);

        if( get_x_id(&discover_packet) != get_x_id(&offer_packet) ) {
            printf("Ignoring offer with XID 0x%08X\n", ntohl(offer_packet.xid));
            continue;
        }
        
        memcpy(&last_offer_packet, &offer_packet, received_bytes);

    } // End of while(1) for receiving packets

    if(!full_dora)
        exit(0);

    
    //
    // Send the DHCPREQUEST
    // Note: If there were multiple offers we reply to the last one received
    //

    dhcp_packet_t request_packet;
    memset(&request_packet, 0, sizeof(request_packet));

    uint32_t req_ip = get_offered_ip(&last_offer_packet);
    uint32_t dhcp_server = get_dhcp_server_ip(&last_offer_packet);
    uint32_t xid = get_x_id(&discover_packet); // Get the XID from the discover packet in case there are other OFFERS flying around

    size_t request_packet_size = create_request_packet(&request_packet, client_mac, xid, &req_ip, &dhcp_server);
    if(verbose) {
        if(use_raw)
            raw_dump_dhcp_packet(&request_packet);
        else
            dump_dhcp_packet(&request_packet, request_packet_size);
    }


    printf("Sending DHCPREQUEST (XID: 0x%08X) to 255.255.255.255...\n", ntohl(request_packet.xid));
    if (sendto(sockfd, &request_packet, request_packet_size, 0,
            (struct sockaddr *)&server_addr_broadcast, sizeof(server_addr_broadcast)) < 0) {
        perror("sendto failed");
        close(sockfd);
        exit(EXIT_FAILURE);
    }
    
    /* Receive and Parse DHCPACK  Reply */
    
    dhcp_packet_t ack_packet;
    
    printf("Waiting for DHCPACK...\n");
    memset(&ack_packet, 0, sizeof(ack_packet)); // Clear buffer for next packet
    received_bytes = recvfrom(sockfd, &ack_packet, sizeof(ack_packet), 0,
                            (struct sockaddr *)&source_addr, &source_addr_len);

    if (received_bytes < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) { // EAGAIN/EWOULDBLOCK for non-blocking timeout
            printf("Receive timeout. No more offers.\n");
        } else {
            perror("recvfrom failed");
        }
    } 

    if(verbose) {
        if(use_raw)
            raw_dump_dhcp_packet(&ack_packet);
        else
            dump_dhcp_packet(&ack_packet, received_bytes);
    } 
    print_packet_info(&ack_packet, received_bytes);
    

    //
    // Send the DHCPRELEASE
    //

    dhcp_packet_t release_packet;
    memset(&release_packet, 0, sizeof(release_packet));

    // We have req_ip, dhcp_server, and xid alreayd defined

    size_t release_packet_size = create_release_packet(&release_packet, client_mac, xid, &req_ip, &dhcp_server);
    if(verbose) {
        if(use_raw)
            raw_dump_dhcp_packet(&release_packet);
        else
            dump_dhcp_packet(&release_packet, release_packet_size);
    }

    printf("Sending DHCPRELEASE (XID: 0x%08X) to 255.255.255.255...\n", ntohl(request_packet.xid));
    if (sendto(sockfd, &request_packet, request_packet_size, 0,
            (struct sockaddr *)&server_addr_broadcast, sizeof(server_addr_broadcast)) < 0) {
        perror("sendto failed");
        close(sockfd);
        exit(EXIT_FAILURE);
    }

    /*
     * Cleanup
     */
    close(sockfd);

    return 0;
}
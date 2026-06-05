# Informe Técnico — MAC Flooding Attack
**Nombre:** Reymond Marte  
**Matrícula:** 2025-0684  
**Asignatura:** Seguridad en Redes  
**Práctica:** P5 — MAC Flooding  

---
Link de demostracion: https://youtu.be/cI2i6wS0bbo?si=GRmAHj_Ri7FpKhOd
## 1. Objetivo del Laboratorio

Demostrar cómo un atacante puede agotar la tabla CAM (Content Addressable Memory) de un switch mediante el envío masivo de frames Ethernet con MACs de origen aleatorias, forzando al switch a actuar como un hub y hacer flooding de todo el tráfico a todos los puertos, y documentar la contramedida correspondiente para mitigar el ataque.

---

## 2. Objetivo del Script

El script `mac_flooding.py` genera frames Ethernet con MACs de origen completamente aleatorias a máxima velocidad. Cada frame fuerza al switch a registrar una nueva entrada en su tabla CAM. Cuando la tabla se agota, el switch no puede determinar a qué puerto enviar cada frame y realiza flooding a todos los puertos, permitiendo al atacante capturar tráfico ajeno.

### 2.1 Parámetros del Script

| Flag | Parámetro | Descripción | Default |
|---|---|---|---|
| `-i` | Interfaz | Interfaz de red del atacante | Requerido |
| `-c` | Cantidad | Frames a enviar (0 = infinito) | 1000 |
| `-d` | Delay | Segundos entre frames | 0.001 |
| `-v` | Verbose | Muestra detalle de cada frame | False |

### 2.2 Requisitos

| Requisito | Detalle |
|---|---|
| Sistema operativo | Linux |
| Python | 3.x |
| Librería | Scapy: `pip install scapy` |
| Permisos | Root: `sudo` |
| Conectividad | Mismo dominio L2 que el switch objetivo |
| Entorno | Laboratorio controlado |

---

## 3. Funcionamiento del Script

### 3.1 Descripción por Función

**`random_mac()`**  
Genera una MAC aleatoria unicast con prefijo `02:xx` para garantizar que el switch intente aprenderla como una entrada válida en su tabla CAM.

**`build_frame()`**  
Construye un frame Ethernet con MAC de origen y destino aleatorias, más un payload aleatorio de entre 20 y 100 bytes para simular tráfico real. El switch aprende la MAC de origen y la agrega a su tabla CAM.

**`mac_flood(iface, count, delay, verbose)`**  
Función principal del ataque. Genera y envía frames en loop hasta alcanzar el límite configurado. Muestra estadísticas de tasa de envío en tiempo real cada 200 frames.

**`signal_handler(sig, frame)`**  
Captura `SIGINT` (Ctrl+C) y muestra estadísticas finales del ataque antes de terminar.

### 3.2 Ejecución

```bash
# Ataque infinito a máxima velocidad
sudo python3 mac_flooding.py -i ens3 -c 0 -d 0

# Ataque con 5000 frames
sudo python3 mac_flooding.py -i ens3 -c 5000 -d 0.001
```

---

## 4. Documentación de la Red

### 4.1 Topología

> Ver screenshot adjunto de la topología en PNetLab.
![[Pasted image 20260604215847.png]]
### 4.2 Direccionamiento IP

| Dispositivo | Interfaz | IP | Rol |
|---|---|---|---|
| Router | e0/0 | 192.6.84.1 | Gateway |
| Atacante | ens3 | 192.6.84.10 | Atacante |
| Víctima | eth0 | 192.6.84.15 | Víctima |
| VPCs | eth0 | DHCP | Hosts adicionales |
| SW1 | — | Solo L2 | Switch objetivo |
| SW2 | — | Solo L2 | Switch STP |
| SW3 | — | Solo L2 | Switch STP |

### 4.3 Detalles de Red

| Parámetro | Valor |
|---|---|
| Red | 192.6.84.0/24 |
| Máscara | 255.255.255.0 |
| Gateway | 192.6.84.1 |
| VLAN | VLAN 1 (default) |
| Plataforma | PNetLab |

### 4.4 Requisitos de Red

- Atacante conectado al switch objetivo (SW1, puerto e0/3)
- Sin Port Security configurado en el switch
- Red de laboratorio aislada

---

## 5. Demostración del Ataque

### 5.1 Verificación Inicial

Estado de la tabla CAM antes del ataque:
```cisco
SW1# show mac address-table count
```
```
Mac Entries for Vlan 1:
Dynamic Address Count : 4
Total Mac Addresses   : 4
Total Mac Address Space Available: 221571720
```

### 5.2 Ejecución del Ataque

```bash
sudo python3 mac_flooding.py -i ens3 -c 0 -d 0
```

### 5.3 Verificación del Efecto

Tabla CAM durante el ataque:
```cisco
SW1# show mac address-table count
```
```
Mac Entries for Vlan 1:
Dynamic Address Count : 5451
Total Mac Addresses   : 5451
```

> En segundos, la tabla CAM pasó de 4 entradas legítimas a 5,451 entradas falsas inyectadas por el atacante. El switch comienza a realizar flooding de todo el tráfico a todos los puertos.

### 5.4 Indicadores de Ataque

| Indicador | Descripción |
|---|---|
| Contador CAM disparado | `Dynamic Address Count` sube abruptamente |
| MACs aleatorias en tabla | Entradas con prefijo `02:xx` no asociadas a hosts reales |
| Tráfico en todos los puertos | El switch actúa como hub, flooding a todos |
| Degradación de rendimiento | Aumento de carga en el switch por procesamiento masivo |

---

## 6. Contramedida — Port Security

### 6.1 Descripción

Port Security es una función de seguridad configurada por interfaz en el switch que limita la cantidad de MACs permitidas por puerto. Si se detecta un exceso de MACs, el switch aplica la acción de violación configurada — en este caso, apagar el puerto automáticamente (`shutdown`).

### 6.2 Configuración en SW1

**Activar Port Security en el puerto del atacante (e0/3):**
```cisco
SW1(config)# interface e0/3
SW1(config-if)# switchport mode access
SW1(config-if)# switchport port-security
SW1(config-if)# switchport port-security maximum 5
SW1(config-if)# switchport port-security violation shutdown
SW1(config-if)# switchport port-security mac-address sticky
SW1(config-if)# exit
```

> `sticky` aprende automáticamente las MACs legítimas y las fija, sin necesidad de configurarlas manualmente.

### 6.3 Modos de Violación

| Modo | Acción | Genera Log |
|---|---|---|
| `shutdown` | Apaga el puerto (err-disabled) | ✅ |
| `restrict` | Descarta MACs extras, puerto activo | ✅ |
| `protect` | Descarta MACs extras silenciosamente | ❌ |

### 6.4 Verificación

```cisco
SW1# show port-security
SW1# show port-security interface e0/3
SW1# show mac address-table count
```

### 6.5 Resultado

Con Port Security activo, al lanzar el ataque el puerto entra en `err-disabled` automáticamente:

```
Port Security              : Enabled
Port Status                : Secure-shutdown
Violation Mode             : Shutdown
Maximum MAC Addresses      : 5
Security Violation Count   : 1
Last Source Address:Vlan   : 02ec.8555.bc08:1
```

El ataque queda bloqueado y la tabla CAM se mantiene con solo las entradas legítimas.

### 6.6 Restaurar Puerto tras Violación

```cisco
SW1(config)# interface e0/3
SW1(config-if)# shutdown
SW1(config-if)# no shutdown
```

---

## 7. Conclusión

El ataque MAC Flooding explota el tamaño limitado de la tabla CAM del switch para forzarlo a actuar como un hub, exponiendo el tráfico de todos los hosts conectados. La contramedida más efectiva es Port Security, que limita la cantidad de MACs permitidas por puerto y apaga automáticamente el puerto del atacante al detectar el exceso, bloqueando el ataque en tiempo real.

---

*Reymond Marte — 2025-0684*

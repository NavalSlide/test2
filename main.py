import asyncio
import logging
import csv
import random
import io
from playwright.async_api import async_playwright
import os
from datetime import datetime
from dotenv import load_dotenv
import argparse

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_activity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración por defecto
DEFAULT_URL = os.getenv('YOUTUBE_URL', 'https://www.youtube.com/watch?v=zVAnXmQOisc')
DEFAULT_VIEWS = int(os.getenv('TARGET_VIEWS', '1000000'))
DEFAULT_CONCURRENCY = int(os.getenv('CONCURRENCY', '10'))
DEFAULT_MIN_VIEW_TIME = int(os.getenv('MIN_VIEW_TIME', '15'))
DEFAULT_MAX_VIEW_TIME = int(os.getenv('MAX_VIEW_TIME', '30'))

# Parseador de la lista de proxies
def parse_proxies_csv(csv_content):
    proxies = []
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    for row in csv_reader:
        ip = row.get('ip', '').strip('"')
        port = row.get('port', '').strip('"')
        protocol = row.get('protocols', '').strip('"').split(',')[0]  # Usar el primer protocolo si hay varios
        country = row.get('country', '').strip('"')
        
        # Solo incluir proxies con IP, puerto y protocolo válidos
        if ip and port and protocol:
            # Convertir el formato del protocolo para que sea compatible con Playwright
            proxy_protocol = protocol.lower()
            if proxy_protocol == 'socks4':
                proxy_protocol = 'socks5'  # Playwright no soporta socks4 directamente, usamos socks5
            
            proxy = {
                'ip': ip,
                'port': port,
                'protocol': proxy_protocol,
                'country': country,
                'url': f"{proxy_protocol}://{ip}:{port}"
            }
            proxies.append(proxy)
    
    logger.info(f"Cargados {len(proxies)} proxies de la lista CSV")
    return proxies

# Usar la lista de proxies proporcionada
PROXY_CSV = """ip,anonymityLevel,asn,country,isp,latency,org,port,protocols,speed,upTime,upTimeSuccessCount,upTimeTryCount,updated_at,responseTime
"72.250.31.148","elite","AS21928","US","T-Mobile USA, Inc.","148","T-Mobile USA, Inc.","80","socks4","1","98","313","318","2025-03-12T05:12:34.080Z","291"
"115.127.107.218","elite","AS24342","BD","BRACNet Limited","158","BRACNet Limited","1085","socks5","1","58","1458","2496","2025-03-12T05:12:34.081Z","4285"
"78.83.237.146","elite","AS8717","BG","A1 Bulgaria EAD","81","Spectrum","4153","socks4","1","99","2419","2440","2025-03-12T05:12:34.074Z","352"
"168.205.217.58","elite","AS264869","BR","SPEED MAX TELECOMUNICAÇÕES LTDA ME","222","SPEED MAX TELECOMUNICAÇÕES LTDA ME","4145","socks4","1","88","8128","9250","2025-03-12T05:12:34.367Z","4208"
"217.23.76.142","elite","AS15974","RU","VTT-0 (Saratov Part-I)","62","JSC Volgatranstelecom","10001","socks4","1","29","2648","9169","2025-03-12T05:12:34.285Z","3390"
"185.143.234.28","elite","AS205585","IR","Noyan Abr Arvan Co. ( Private Joint Stock)","3","Anycast","8080","socks4","1","98","8874","9032","2025-03-12T05:12:34.077Z","1287"
"27.147.139.73","elite","AS23688","BD","Link3 Technologies Limited","154","Corporate Subscriber","4145","socks4","1","97","8961","9257","2025-03-12T05:12:34.368Z","1903"
"95.216.57.120","transparent","AS24940","FI","Hetzner Online GmbH","32","N/A","8292","http","8312","100","37","37","2025-03-12T05:12:34.085Z","314"
"46.98.185.160","elite","AS15377","UA","ISP \"Fregat\"","114","N/A","5678","socks4","1","39","982","2545","2025-03-12T05:12:34.075Z","1314"
"49.0.87.62","elite","AS133481","TH","AIS-Fibre","198","N/A","8088","http","20403","100","67","67","2025-03-12T05:12:34.071Z","1390"
"185.56.180.14","elite","AS206866","ES","GARTEL","41","Gartel","5678","socks4","1","100","9284","9286","2025-03-12T05:12:34.366Z","3598"
"192.181.69.47","elite","AS10796","US","Spectrum","117","Time Warner Cable Internet LLC","5678","socks4","1","16","1469","9293","2025-03-12T05:12:34.068Z","2789"
"185.189.208.65","elite","AS51142","GE","LLC Ekspres Netvork","59","ExpressNet","4153","socks4","1","99","9234","9287","2025-03-12T05:12:34.369Z","1210"
"109.236.84.101","elite","AS49981","NL","WorldStream B.V.","10","Worldstream","30090","socks5","1","100","9147","9154","2025-03-12T05:12:34.367Z","1213"
"66.33.212.173","elite","AS26347","US","New Dream Network, LLC","14","New Dream Network, LLC","17567","socks4","1","16","1498","9203","2025-03-12T05:12:34.082Z","396"
"183.88.214.58","elite","AS45629","TH","Triple T Broadband Public Company Limited","210","Triple T Broadband Public Company Limited","5678","socks4","1","91","8395","9240","2025-03-12T05:12:34.066Z","3702"
"193.70.113.238","elite","AS16276","FR","OVH SAS","6","OVH","18545","socks5","1","100","9242","9242","2025-03-12T05:12:34.366Z","902"
"197.234.13.4","elite","AS36902","SC","Intelvision","123","Intelvision Ltd","4145","socks4","84","99","9092","9141","2025-03-12T05:12:34.067Z","75"
"185.220.226.108","elite","AS205585","TR","Noyan Abr Arvan Co. ( Private Joint Stock)","89","Noyan Abr Arvan Co. ( Private Joint Stock)","3128","socks4","1","86","7922","9239","2025-03-12T05:12:34.068Z","989"
"4.14.120.230","elite","N/A","US","Level 3","129","N/A","39593","socks4","1","99","1754","1770","2025-03-12T05:12:33.985Z","256"
"178.79.144.186","elite","AS63949","GB","Linode","14","Linode, LLC","8080","socks5","1","100","9220","9222","2025-03-12T05:12:33.985Z","2188"
"178.32.143.55","elite","AS16276","FR","OVH ISP","14","OVH Srl","32048","socks4","1","100","2515","2516","2025-03-12T05:12:17.266Z","5385"
"95.140.124.161","elite","AS9125","RS","Drustvo za telekomunikacije Orion telekom doo Beograd, Gandijeva 76a","26","Orion Telekom Network","1080","socks4","1","100","9218","9228","2025-03-12T05:12:17.170Z","3905"
"49.0.42.114","elite","AS38744","BD","Always On Network Bangladesh Ltd.","178","Always On Network Bangladesh Ltd","10801","socks4","85","98","9089","9239","2025-03-12T05:12:17.171Z","470"
"113.203.234.42","elite","AS9387","PK","SHARP TELECOM (PRIVATE) LIMITED","126","Telecom Services","5678","socks4","82","48","1184","2478","2025-03-12T05:12:17.266Z","2310"
"81.12.124.185","elite","AS42337","IR","Respina Networks & Beyond PJSC","113","Respina Networks","5678","socks5","1","80","7387","9252","2025-03-12T05:12:17.268Z","71"
"151.80.33.46","elite","AS16276","FR","OVH SAS","14","OVH SAS","7497","socks5","1","100","9216","9217","2025-03-12T05:12:17.169Z","1405"
"185.169.181.11","elite","AS34984","TR","Ates Dc","48","Ibrahim MALA trading as Ates Dc","4145","socks4","1","100","9222","9258","2025-03-12T05:12:17.169Z","4185"
"37.152.171.39","elite","AS198569","IR","Rahanet Zanjan Co. (Private Joint-Stock)","184","Rahanet Zanjan Co.","4153","socks4","1","50","4593","9256","2025-03-12T05:12:17.168Z","752"
"138.36.171.244","elite","AS262300","BR","Super Connect Telecom Ltda","185","Super Connect Telecom Ltda","7497","socks5","1","59","5390","9209","2025-03-12T05:12:17.267Z","1971"
"79.143.190.221","elite","AS51167","DE","Contabo GmbH","11","Contabo GmbH","12580","socks5","1","100","9205","9207","2025-03-12T05:12:17.270Z","4112"
"89.254.243.37","elite","AS12389","RU","PJSC Rostelecom","822","Adsl Kirov","7788","socks5","1","50","1164","2340","2025-03-12T05:12:16.976Z","3491"
"200.119.141.114","transparent","AS13682","GT","Telgua","166","TELECOMUNICACIONES DE GUATEMALA, SOCIEDAD ANONIMA","999","http","28295","100","50","50","2025-03-12T05:12:16.883Z","41"
"80.234.51.0","elite","AS12389","RU","Rostelecom networks","54","JSC VolgaTelecom Samara branch","7788","socks5","81","45","1064","2342","2025-03-12T05:12:16.967Z","349"
"95.64.144.66","elite","AS8359","RU","MTS PJSC","45","Customers P2P 2022 00 WAN","1080","socks4","1","100","9273","9283","2025-03-12T05:12:16.978Z","73"
"104.17.9.114","elite","AS13335","US","Cloudflare, Inc.","3","Cloudflare, Inc.","80","socks4","1","100","9196","9197","2025-03-12T05:12:16.973Z","4490"
"167.103.19.22","elite","AS53813","IN","ZSCALER, INC.","129","Zscaler Softech India Private Limited","11194","socks4","1","99","1843","1864","2025-03-12T05:12:16.967Z","3394"
"46.29.116.6","elite","AS44963","RU","KMVtelecom","63","Joint Stock company \"KMVtelecom\"","4145","socks4","81","73","1754","2388","2025-03-12T05:12:16.974Z","4207"
"83.143.29.225","elite","AS37678","BW","BOTSWANA FIBRE NETWORKS (Proprietary) Limited","191","Vbn Corp","1080","socks4","1","99","2186","2207","2025-03-12T05:12:16.974Z","4510"
"61.7.183.101","elite","AS131090","TH","CAT Telecom Public Company Limited","205","National Telecom Public Company Limited","4145","socks4","1","88","8114","9188","2025-03-12T05:12:16.971Z","3492"
"171.253.61.51","elite","AS7552","VN","Viettel Corporation","288","VIETEL","1080","socks4","1","75","1781","2364","2025-03-12T05:12:16.970Z","356"
"89.218.185.93","elite","AS9198","KZ","JSC Kazakhtelecom","97","Hospispavlodarskoioblasti","8082","socks4","1","100","1835","1838","2025-03-12T05:12:16.883Z","1196"
"78.133.163.190","elite","AS12912","PL","T-Mobile PL ICT","22","N/A","4145","socks4","1","99","622","628","2025-03-12T05:12:16.881Z","1285"
"103.131.104.125","elite","AS59151","ID","Diskominfo DIY","196","Diskominfo DIY","10800","socks5","81","95","2317","2432","2025-03-12T05:12:16.885Z","3810"
"104.248.158.78","elite","N/A","SG","DigitalOcean, LLC","177","N/A","53878","socks4","1","99","1580","1593","2025-03-12T05:11:56.585Z","2418"
"47.113.219.226","elite","AS37963","CN","Hangzhou Alibaba Advertising Co., Ltd.","193","Aliyun Computing Co., LTD","9090","socks4","1","99","1442","1457","2025-03-12T05:11:56.470Z","1299"
"201.68.215.79","elite","AS27699","BR","Vivo","204","TELEF�NICA BRASIL S.A","61221","socks4","1","6","539","9281","2025-03-12T05:11:56.667Z","983"
"140.250.148.19","elite","AS4134","CN","Chinanet","170","Chinanet SD","1080","socks4","1","63","5807","9207","2025-03-12T05:11:56.668Z","5082"
"172.104.49.195","elite","AS63949","SG","Akamai Technologies","256","Linode","8080","socks4","1","99","1796","1810","2025-03-12T05:11:56.585Z","5197"
"168.119.209.189","elite","AS24940","DE","Hetzner Online GmbH","8","Hetzner","60006","socks5","1","94","8654","9240","2025-03-12T05:11:56.668Z","4902"
"123.108.98.108","elite","AS45313","ID","PEMDA-NAD","218","N/A","5678","socks4","1","90","2279","2541","2025-03-12T05:11:56.584Z","2807"
"8.42.71.1","elite","AS399869","US","Mountain Broadband","124","Level 3, LLC","39593","socks4","1","100","1866","1868","2025-03-12T05:11:56.466Z","5006"
"108.59.14.200","elite","AS30633","US","Leaseweb USA, Inc.","83","Leaseweb USA, Inc.","13402","socks4","1","91","1932","2112","2025-03-12T05:11:56.669Z","4303"
"209.13.96.171","elite","AS10834","AR","Telefonica de Argentina","225","Telefonica de Argentina","39921","socks4","1","99","2158","2189","2025-03-12T05:11:56.476Z","2811"
"171.228.130.87","elite","AS7552","VN","Viettel Corporation","390","VIETEL","23136","socks4","1","63","637","1018","2025-03-12T05:11:56.471Z","2297"
"75.119.205.47","elite","AS26347","US","New Dream Network, LLC","149","New Dream Network, LLC","49252","socks5","1","81","7471","9216","2025-03-12T05:11:56.470Z","990"
"""
PROXIES = parse_proxies_csv(PROXY_CSV)

# Lista de user agents populares para rotar
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/119.0 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0"
]

async def view_video(url, proxy=None, user_agent=None, view_duration_range=(15, 30), retry_count=0):
    """Ver un video de YouTube con configuraciones personalizadas"""
    max_retries = 2
    proxy_info = None
    
    if proxy:
        proxy_info = f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
        logger.info(f"Usando proxy: {proxy_info} ({proxy['country']})")
    
    async with async_playwright() as p:
        browser_type = p.chromium
        
        # Configuración del navegador
        browser_args = ['--disable-blink-features=AutomationControlled']
        
        # Configurar proxy si está disponible
        browser_kwargs = {'headless': True, 'args': browser_args}
        if proxy_info:
            browser_kwargs['proxy'] = {'server': proxy_info}
        
        try:
            # Lanzar navegador
            browser = await browser_type.launch(**browser_kwargs)
            
            # Crear contexto con user agent personalizado
            context = await browser.new_context(
                user_agent=user_agent or random.choice(USER_AGENTS),
                viewport={'width': 1280, 'height': 720}
            )
            
            # Configurar cookies para simular que el usuario ya ha visitado YouTube antes
            await context.add_cookies([{
                'name': 'CONSENT', 
                'value': 'YES+', 
                'domain': '.youtube.com',
                'path': '/'
            }])
            
            # Crear nueva página
            page = await context.new_page()
            
            # Configurar timeouts
            page.set_default_timeout(60000)
            
            # Ir a YouTube
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                logger.info(f"Página cargada: {url}")
                
                # Verificar si el video se está reproduciendo
                video_elem = await page.wait_for_selector('video', timeout=10000)
                if video_elem:
                    logger.info("Video encontrado")
                    
                    # Eliminar anuncios si aparecen
                    try:
                        skip_ad_button = await page.wait_for_selector('.ytp-ad-skip-button', timeout=5000)
                        if skip_ad_button:
                            await skip_ad_button.click()
                            logger.info("Anuncio saltado")
                    except:
                        pass  # No hay anuncio o no se puede saltar
                    
                    # Dar play al video si está pausado
                    try:
                        await page.evaluate("""
                            var video = document.querySelector('video');
                            if (video && video.paused) {
                                video.play();
                            }
                        """)
                    except:
                        logger.warning("No se pudo reproducir el video automáticamente")
                    
                    # Simular interacción humana: mover el ratón aleatoriamente
                    for _ in range(3):
                        x = random.randint(100, 1000)
                        y = random.randint(100, 600)
                        await page.mouse.move(x, y)
                        await asyncio.sleep(random.uniform(0.5, 2.0))
                    
                    # Ajustar volumen
                    try:
                        await page.evaluate("""
                            var video = document.querySelector('video');
                            if (video) {
                                video.volume = 0.2;
                            }
                        """)
                    except:
                        pass
                    
                    # Duración de visualización aleatoria
                    view_time = random.uniform(view_duration_range[0], view_duration_range[1])
                    logger.info(f"Viendo video durante {view_time:.2f} segundos")
                    
                    # En lugar de esperar pasivamente, hacemos scroll aleatorio cada 5-10 segundos
                    view_start = datetime.now()
                    elapsed = 0
                    
                    while elapsed < view_time:
                        await asyncio.sleep(random.uniform(5, 10))
                        
                        # Hacer scroll aleatorio
                        scroll_y = random.randint(-300, 300)
                        await page.mouse.wheel(0, scroll_y)
                        
                        # Verificar si todavía estamos viendo el video
                        try:
                            playing = await page.evaluate("""
                                var video = document.querySelector('video');
                                return video && !video.paused;
                            """)
                            if not playing:
                                logger.warning("El video se detuvo, intentando reanudar")
                                await page.evaluate("""
                                    var video = document.querySelector('video');
                                    if (video && video.paused) {
                                        video.play();
                                    }
                                """)
                        except:
                            pass
                        
                        elapsed = (datetime.now() - view_start).total_seconds()
                    
                    logger.info(f"Visualización completada: {view_time:.2f} segundos")
                    return True
                else:
                    logger.error("No se encontró el elemento de video")
            except Exception as e:
                logger.error(f"Error al cargar la página o el video: {str(e)}")
                if retry_count < max_retries:
                    logger.info(f"Reintentando ({retry_count + 1}/{max_retries})...")
                    return await view_video(url, proxy, user_agent, view_duration_range, retry_count + 1)
                return False
        except Exception as e:
            logger.error(f"Error al iniciar el navegador: {str(e)}")
            if retry_count < max_retries:
                logger.info(f"Reintentando ({retry_count + 1}/{max_retries})...")
                return await view_video(url, proxy, user_agent, view_duration_range, retry_count + 1)
            return False
        finally:
            await browser.close()

async def main():
    parser = argparse.ArgumentParser(description='YouTube View Bot')
    parser.add_argument('--url', type=str, help='URL del video de YouTube', 
                        default=DEFAULT_URL)
    parser.add_argument('--views', type=int, help='Número de vistas a generar', 
                        default=DEFAULT_VIEWS)
    parser.add_argument('--concurrency', type=int, help='Número de navegadores concurrentes', 
                        default=DEFAULT_CONCURRENCY)
    parser.add_argument('--min-view-time', type=int, help='Tiempo mínimo de visualización en segundos', 
                        default=DEFAULT_MIN_VIEW_TIME)
    parser.add_argument('--max-view-time', type=int, help='Tiempo máximo de visualización en segundos', 
                        default=DEFAULT_MAX_VIEW_TIME)
    parser.add_argument('--use-proxies', action='store_true', help='Usar proxies cargados')
    
    args = parser.parse_args()
    
    logger.info(f"Iniciando bot para {args.url}")
    logger.info(f"Objetivo: {args.views} vistas con {args.concurrency} procesos concurrentes")
    
    if args.use_proxies:
        if PROXIES:
            logger.info(f"Usando {len(PROXIES)} proxies cargados")
        else:
            logger.warning("No hay proxies disponibles")
    
    views_completed = 0
    failed_views = 0
    start_time = datetime.now()
    
    # Crear directorio para logs si no existe
    os.makedirs("logs", exist_ok=True)
    
    while views_completed < args.views:
        # Determinar cuántas vistas procesar en este lote
        batch_size = min(args.concurrency, args.views - views_completed)
        tasks = []
        
        for _ in range(batch_size):
            # Seleccionar proxy aleatorio si está habilitado
            proxy = random.choice(PROXIES) if args.use_proxies and PROXIES else None
            
            # Seleccionar user agent aleatorio
            user_agent = random.choice(USER_AGENTS)
            
            # Crear tarea para cada visualización
            task = view_video(
                args.url, 
                proxy=proxy,
                user_agent=user_agent,
                view_duration_range=(args.min_view_time, args.max_view_time)
            )
            tasks.append(task)
        
        # Ejecutar tareas concurrentemente
        results = await asyncio.gather(*tasks)
        successful_views = sum(1 for result in results if result)
        failed_this_batch = batch_size - successful_views
        
        views_completed += successful_views
        failed_views += failed_this_batch
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        views_per_hour = views_completed / (elapsed_time / 3600) if elapsed_time > 0 else 0
        
        logger.info(f"Progreso: {views_completed}/{args.views} vistas completadas ({successful_views} exitosas, {failed_this_batch} fallidas en este lote)")
        logger.info(f"Tasa: {views_per_hour:.2f} vistas por hora, tiempo estimado restante: {((args.views - views_completed) / views_per_hour * 60) if views_per_hour > 0 else 'N/A'} minutos")
        
        # Pequeña pausa entre lotes para evitar detección y dar tiempo al sistema
        delay = random.uniform(1.0, 5.0)
        logger.info(f"Esperando {delay:.2f} segundos antes del siguiente lote...")
        await asyncio.sleep(delay)
    
    total_time = (datetime.now() - start_time).total_seconds()
    hours = total_time / 3600
    
    logger.info(f"¡Completado! {views_completed} vistas generadas en {total_time:.2f} segundos ({hours:.2f} horas)")
    logger.info(f"Tasa final: {views_completed / hours:.2f} vistas por hora")
    logger.info(f"Vistas fallidas: {failed_views} ({(failed_views / (views_completed + failed_views) * 100):.2f}%)")

if __name__ == "__main__":
    # Ejecutar el bucle de eventos de asyncio
    asyncio.run(main())

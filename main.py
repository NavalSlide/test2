#   ░█████╗░██╗██████╗░░█████╗░███╗░░██╗███╗░░██╗
#   ██╔══██╗██║██╔══██╗██╔══██╗████╗░██║████╗░██║
#   ███████║██║██║░░██║███████║██╔██╗██║██╔██╗██║
#   ██╔══██║██║██║░░██║██╔══██║██║╚████║██║╚████║
#   ██║░░██║██║██████╔╝██║░░██║██║░╚███║██║░╚███║
#   ╚═╝░░╚═╝╚═╝╚═════╝░╚═╝░░╚═╝╚═╝░░╚══╝╚═╝░░╚══╝

import time
import random
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import sys
import os

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("viewbot_activity.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Parámetros configurables
link = 'https://www.youtube.com/watch?v=zVAnXmQOisc&t=16s&ab_channel=Pardo18'  # URL del video
views = 1000000  # Número total de vistas objetivo
min_timer = 10  # Tiempo mínimo entre refrescos (segundos)
max_timer = 15  # Tiempo máximo entre refrescos (segundos)
target_duration_hours = 4  # Duración objetivo en horas

# Calcular cuántos refrescos se necesitan para 4 horas
seconds_in_four_hours = target_duration_hours * 60 * 60
avg_refresh_time = (min_timer + max_timer) / 2
min_refreshes_needed = seconds_in_four_hours / avg_refresh_time

# Tomar el mínimo entre las vistas objetivo y los refrescos necesarios para 4 horas
actual_views = min(views, int(min_refreshes_needed))

logger.info(f"Iniciando bot para {link}")
logger.info(f"Objetivo: {actual_views} vistas")
logger.info(f"Tiempo estimado: {actual_views * avg_refresh_time / 3600:.2f} horas")

# Configurar opciones de Chrome
chrome_options = Options()
chrome_options.add_argument("--mute-audio")  # Silenciar audio
chrome_options.add_argument("--disable-infobars")  # Deshabilitar barras de información
chrome_options.add_argument("--disable-extensions")  # Deshabilitar extensiones
chrome_options.add_argument("--disable-gpu")  # Deshabilitar GPU
chrome_options.add_argument("--disable-dev-shm-usage")  # Deshabilitar uso de /dev/shm

# Para ejecutar en segundo plano, descomentar la siguiente línea:
# chrome_options.add_argument("--headless")

# Lista de user agents populares para rotar
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

# Crear directorio para logs si no existe
os.makedirs("logs", exist_ok=True)

try:
    # Configurar user agent aleatorio
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    # Iniciar el navegador
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(link)
    logger.info("Navegador iniciado y página cargada")
    
    # Registrar tiempo de inicio
    start_time = datetime.datetime.now()
    
    for i in range(actual_views):
        # Tiempo aleatorio entre refrescos para parecer más humano
        timer = random.uniform(min_timer, max_timer)
        
        # Dormir durante el tiempo establecido
        time.sleep(timer)
        
        # Refrescar la página
        driver.refresh()
        
        # Calcular estadísticas
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
        views_per_hour = (i + 1) / (elapsed_time / 3600) if elapsed_time > 0 else 0
        estimated_completion_time = (actual_views - (i + 1)) / views_per_hour if views_per_hour > 0 else 0
        
        # Registrar progreso
        logger.info(f"Vista #{i+1}/{actual_views} completada (tiempo entre refrescos: {timer:.2f}s)")
        logger.info(f"Tasa: {views_per_hour:.2f} vistas/hora, tiempo estimado restante: {estimated_completion_time:.2f} horas")
        
        # Si hemos superado las 4 horas, mostrar un mensaje pero continuar
        if elapsed_time >= seconds_in_four_hours and i < actual_views - 1:
            logger.info(f"¡Se han alcanzado {target_duration_hours} horas de ejecución! Continuando...")

except Exception as e:
    logger.error(f"Error: {str(e)}")
finally:
    try:
        # Cerrar el navegador al finalizar
        driver.quit()
        logger.info("Navegador cerrado")
    except:
        pass
    
    # Mostrar estadísticas finales
    try:
        end_time = datetime.datetime.now()
        total_time = (end_time - start_time).total_seconds()
        logger.info(f"¡Completado! Bot ejecutado durante {total_time/3600:.2f} horas")
        logger.info(f"Vistas totales: {i+1}")
        logger.info(f"Tasa final: {(i+1)/(total_time/3600):.2f} vistas/hora")
    except:
        pass

logger.info("Programa finalizado")

#   ░█████╗░██╗██████╗░░█████╗░███╗░░██╗███╗░░██╗
#   ██╔══██╗██║██╔══██╗██╔══██╗████╗░██║████╗░██║
#   ███████║██║██║░░██║███████║██╔██╗██║██╔██╗██║
#   ██╔══██║██║██║░░██║██╔══██║██║╚████║██║╚████║
#   ██║░░██║██║██████╔╝██║░░██║██║░╚███║██║░╚███║
#   ╚═╝░░╚═╝╚═╝╚═════╝░╚═╝░░╚═╝╚═╝░░╚══╝╚═╝░░╚══╝
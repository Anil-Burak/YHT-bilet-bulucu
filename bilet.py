from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from winreg import *


def bilet_al(nereden, nereye, tarih, saat):
    options = Options()
    options.add_experimental_option("detach", True)
    with OpenKey(HKEY_CURRENT_USER,  # Varsayılan tarayıcı bulmak için (Windows için)
                 r"Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice") as key:
        browser = QueryValueEx(key, 'Progid')[0]
    if browser == "MSEdgeHTM":
        driver = webdriver.Edge(options=options)
    else:
        driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://ebilet.tcddtasimacilik.gov.tr/")
        neredenButon = driver.find_element(By.ID, "fromTrainInput")
        neredenButon.click()
        neredenButon.send_keys(nereden)
        neredenSehir = driver.find_element(By.CLASS_NAME, "textLocation")
        neredenSehir.click()
        nereyeButon = driver.find_element(By.ID, "toTrainInput")
        nereyeButon.click()
        nereyeButon.send_keys(nereye)

        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.dropdown-item.station"))
        )

        butonlar = driver.find_elements(By.CSS_SELECTOR, "button.dropdown-item.station")
        for buton in butonlar:
            if buton.is_displayed():
                buton.click()
                break

        driver.find_element(By.CSS_SELECTOR, 'div.datePickerInput').click()
        # TARİH
        tarih = driver.find_element(By.CSS_SELECTOR, f'td[data-date="2025-{tarih}"]')
        driver.execute_script("arguments[0].click();", tarih)

        driver.find_element(By.ID, "searchSeferButton").click()  # Sefer ara

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "p.price"))
        )
        sefer = driver.find_element(By.CSS_SELECTOR, f'time[datetime="{saat}"]')
        sefer.click()  # seferi seçme
        return None
    except Exception as e:
        print(e)
        return None
    finally:
        pass


if __name__ == "__main__":
    bilet_al("Ankara", "Gebze", "03-10", "18:30")

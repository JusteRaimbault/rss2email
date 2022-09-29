
from subprocess import PIPE, Popen

from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common import action_chains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
# run X system before running selenium server (on ABMCitiesFirms DataCollection) https://gist.github.com/alonisser/11192482

def get_element(driver,element,attribute,attribute_value):
    return(driver.find_element_by_xpath("//"+element+"[@"+attribute+"='"+attribute_value+"']"))



def get_element_by_index(driver, element, index):
    return(driver.find_element_by_xpath("(//"+element+")["+str(index)+"]"))


def fill_field(driver,element,value):
    element.clear()
    element.send_keys(value)

def click(driver,element):
    action_chains.ActionChains(driver).click(element).perform()

def click_validate(driver,element,attribute,attribute_value):
    get_element(driver,element,attribute,attribute_value).send_keys(Keys.ENTER)

def wait_for_element(driver,element,attribute,attribute_value,timeout=1000):
    WebDriverWait(driver, timeout).until(expected_conditions.presence_of_element_located((By.XPATH, "//"+element+"[@"+attribute+"='"+attribute_value+"']")))


#opts = FirefoxOptions()
#opts.add_argument("--headless")

EMAIL=open(".email").read()
PWD=open(".pwd").read()

p = Popen(["python", "-u", "test_oauth2.py", "--noauth_local_webserver"], stdin=PIPE, stdout=PIPE, bufsize=1)
for i in range(3):
    p.stdout.readline()
rawadr = p.stdout.readline().decode().strip()
print(rawadr)

# use selenium to connect manually
profile=webdriver.FirefoxProfile()
#driver = webdriver.Firefox(firefox_profile=profile, options=opts)
driver = webdriver.Firefox(firefox_profile=profile)
driver.delete_all_cookies()
driver.get(rawadr)
fill_field(driver,get_element_by_index(driver, 'input', 1),EMAIL)

print(get_element_by_index(driver,'input',1).get_attribute('data-initial-value'))
print(get_element_by_index(driver, 'button', 4).get_attribute('innerHTML'))

#click(driver,get_element_by_index(driver, 'button', 4))
get_element_by_index(driver, 'button', 4).send_keys(Keys.ENTER)
#print(get_element(driver,'input','id','identifierId').get_attribute('innerHTML'))

wait_for_element(driver, 'input', 'name', 'password')

print(get_element_by_index(driver,'button',4).get_attribute('innerHTML'))

fill_field(driver,'input','name','password',PWD)
click(driver,get_element_by_index(driver, 'button', 2))
WebDriverWait(driver, timeout).until(expected_conditions.presence_of_element_located((By.XPATH, "//span[text()='Continuer']")))
print(get_element_by_index(driver,'button',2).get_attribute('innerHTML'))




#p.stdin.write("junktoken\n".encode())
#p.stdin.flush()
#p.stdin.write("\n".encode())
#p.stdout.readline()
#print(p.stdout.readline())

#print(p.communicate(b'n\n')[0])


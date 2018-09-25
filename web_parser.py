import json
import requests
from bs4 import BeautifulSoup

def main():
    pass  # your code here!

    page = requests.get("http://ca.healthinspections.us/napa/search.cfm?start=1&1=1&sd=01/01/1970&ed=03/"
                        "01/2017&kw1=&kw2=&kw3=&rel1=N.permitName&rel2=N.permitName&rel3=N.permitName&zc=&dtRng=YES&pre=similar")
    soup = BeautifulSoup(page.content, 'html.parser')
    results_page = soup.find_all('a', {"class":"buttN", "style":"padding:1px;"})

    inspection_data = []
    print("page 1" + "\n")
    counter = get_results(page, soup, inspection_data, 1)

    '''optional: gathers information on every inspection for every facility for all the other results pages (2 - 138) on the 
    Napa Valley Health Department Website'''

    '''for i in range(1, 138):
        print("page " + str(i + 1) + "\n")
        link = results_page[i]['href']
        page = requests.get("http://ca.healthinspections.us/napa/" + link)
        soup = BeautifulSoup(page.content, 'html.parser')
        counter = get_results(page, soup, inspection_data, counter)'''

    '''writes the json object inspection_data to a text file'''
    with open("inspection_info.txt", 'w+') as outfile:
        json.dump(inspection_data, outfile)


def get_results(page, soup, inspection_data, counter):
    soup = BeautifulSoup(page.content, 'html.parser')
    facilities = soup.find_all('div', {'style': "padding:2px;border-top:1px solid #EFEFEF;"})
    for facility in facilities:

        info = facility.get_text().replace("\t", "").replace("\r", "").strip().split("\n")

        link = facility.find('a')['href']
        page2 = requests.get("http://ca.healthinspections.us/napa/" + link)  # only the latest inspeciton
        soup2 = BeautifulSoup(page2.content, 'html.parser')

        next_link = soup2.find_all('div', {'style': "background-color:#990000;color:#FFFFFF;padding-left:5px;"})[1].find('a')['href']
        page3 = requests.get("http://ca.healthinspections.us/napa/" + next_link)
        soup3 = BeautifulSoup(page3.content, 'html.parser')
        inspections = soup3.find_all('div', {'style': "border:1px solid #E6E67C;width:95%;margin-bottom:10px;"})
        all_inspection_info = dict()

        print("Facility name: " + info[0])
        print("Street address: " + info[5].strip())
        print("City: " + info[6].strip().split(",")[0])
        state_and_zip = info[6].strip().split(",")[1]
        print("State: " + state_and_zip.split(" ")[1])
        print("ZIP Code: " + state_and_zip.split(" ")[2])

        for inspection in inspections:
            info2 = inspection.get_text().replace("\t", "").replace("\r", "").strip().split("\n")
            full_report = inspection.find('div', {'style': "padding:5px;"}).find('a')['href'][3:]
            page4 = requests.get("http://ca.healthinspections.us/" + full_report)
            soup4 = BeautifulSoup(page4.content, 'html.parser')
            inspection_type = soup4.find('div', {'class': 'topSection'}).find('span', {'class': 'blackline',
                                                                                       'style': 'width: 660px;'}).get_text()

            obs_and_corrections = soup4.find('div', {'class': 'page2Content'})
            violation_numbers = obs_and_corrections.find_all('td', {'class': "right"})
            list_of_violations = dict()
            violation_descriptions = soup4.find('table', {'class': 'mainTable'}).find_all('td', {
                "style": "width: 380px; height: 100%;", "valign": "top"})

            for violation_number in violation_numbers:
                number = violation_number.get_text()[0:2]
                description_table = None
                if (int(number) <= 22):
                    description_table = violation_descriptions[0]
                else:
                    description_table = violation_descriptions[1]
                list_of_descriptions = description_table.find_all('tr',
                                                                  {'class': None})  # this only has to be created once
                for description in list_of_descriptions:
                    phrase = description.find('td', {"style": "text-align: left;"}).get_text()
                    if (phrase.split(".")[0] == number):
                        list_of_violations[number] = phrase.split(".")[1].strip()

            date = info2[10].split(": ")[1]
            grade = info2[13]
            inspection_attributes = dict()
            inspection_attributes['Facility name'] = info[0]
            inspection_attributes['Street address'] = info[5].strip()
            inspection_attributes['City'] = info[6].strip().split(",")[0]
            inspection_attributes['State'] = state_and_zip.split(" ")[1]
            inspection_attributes['ZIP Code'] = state_and_zip.split(" ")[2]
            inspection_attributes['Inspection date'] = date
            inspection_attributes['Inspection grade'] = grade
            inspection_attributes['Inspection type'] = inspection_type
            inspection_attributes['violations'] = list_of_violations
            inspection_data.append(inspection_attributes)
            print("inspection #" + str(counter) + ": " + "[Inspection date: " + date + ", Inspection"
                  " grade: " + grade + ", Inspection type: " + inspection_type + ", violations: " +
                  str(list_of_violations) + "]")
            counter = counter + 1

        print("\n")
    return counter

if __name__ == '__main__':
    main()

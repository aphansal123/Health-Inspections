import mysql.connector
from mysql.connector import errorcode
import json

mydb = mysql.connector.connect(host="localhost", auth_plugin='mysql_native_password',
                               passwd="root123", user="root", port=3307, database="mydatabase")

mycursor = mydb.cursor(buffered=True)

''' An optimal SQL schema: There are 3 separate tables, one to store information about each facility, 
one to store general information about each inspection (not including its violations), and one to store each violation
for a particular inspection. The Inspections table uses a foreign key to relate a particular inspection to the facility
where it was conducted, and the Violations table uses a foreign key to relate a particular violation to the inspection
during which it was found. This creates normalized table that avoid repetitive information about the facility for each inspection'''

mycursor.execute("DROP TABLE Violations")
mycursor.execute("DROP TABLE Inspections")
mycursor.execute("DROP TABLE Facilities")

mycursor.execute("CREATE TABLE Facilities ("
                 "  FacilityID int AUTO_INCREMENT PRIMARY KEY NOT NULL, "
                 "  facility_name VARCHAR(255) NOT NULL, "
                 "  street_address VARCHAR(255) NOT NULL, "
                 "  city VARCHAR(255) NOT NULL, "
                 "  state VARCHAR(5) NOT NULL, "
                 "  zip_code VARCHAR(10) NOT NULL)")

mycursor.execute("CREATE TABLE Inspections ("
                 "  InspectionID int AUTO_INCREMENT PRIMARY KEY NOT NULL, "
                 "  FacilityID int NOT NULL, "
                 "  FOREIGN KEY (FacilityID) REFERENCES Facilities (FacilityID), "
                 "  inspection_date VARCHAR(255) NOT NULL, "
                 "  inspection_grade VARCHAR(10) NOT NULL, "
                 "  inspection_type VARCHAR(255) NOT NULL)")

mycursor.execute("CREATE TABLE Violations ("
                 "  id int AUTO_INCREMENT PRIMARY KEY NOT NULL, "
                 "  InspectionID int NOT NULL, "
                 "  FOREIGN KEY (InspectionID) REFERENCES Inspections (InspectionID), "
                 "  itemID VARCHAR(10) NOT NULL, "
                 "  description VARCHAR(255) NOT NULL)")

with open('inspection_info.txt', 'r') as filehandle:
    inspections = json.load(filehandle)

for inspection in inspections:

    facility_entry = list(inspection.values())[0:5] # this should give something in the format [facility_name, address, city, state, zip_code]
    inspection_entry = list(inspection.values())[5:8] # this should give something in the format [inspection date, inspection grade, inspection type]
    try:
        mycursor.execute("SELECT FacilityID FROM Facilities WHERE facility_name = %s AND street_address = %s AND city = %s AND state = %s "
            "AND zip_code = %s", tuple(facility_entry))
        facilityID = mycursor.fetchone()[0]

        #"SELECT facility_name FROM Facilities WHERE FacilityID = %s"
    except:
        mycursor.execute("INSERT INTO Facilities (facility_name, street_address, city, state, zip_code) VALUES (%s, %s, %s, %s, %s)",
                     tuple(facility_entry))
        mydb.commit()
        mycursor.execute("SELECT FacilityID FROM Facilities WHERE facility_name = %s AND street_address = %s AND city = %s AND state = %s "
            "AND zip_code = %s", tuple(facility_entry))
        facilityID = mycursor.fetchone()[0]

    inspection_entry.insert(0, facilityID) # this should give something in the format [facilityID, inspection date, inspection grade, inspection type]

    mycursor.execute("INSERT INTO Inspections (FacilityID, inspection_date, inspection_grade, inspection_type) VALUES (%s, %s, %s, %s)",
                     tuple(inspection_entry))
    mydb.commit()

    violations = list(inspection.values())[8] #this returns a dictionary

    mycursor.execute("SELECT InspectionID FROM Inspections WHERE inspection_date = %s AND inspection_grade = %s AND inspection_type = %s",
                                    (inspection_entry[1], inspection_entry[2], inspection_entry[3]))
    inspectionID = mycursor.fetchone()[0]

    for item in violations:
        description = violations[item]
        mycursor.execute("INSERT INTO Violations (InspectionID, itemID, description) VALUES (%s, %s, %s)", (inspectionID, item, description))
        mydb.commit()

#facility_join = "SELECT Facilities.FacilityID, Inspections.FacilityID FROM Facilities CROSS JOIN Inspections"
#inspection_join = "SELECT Inspections.InspectionID, Violations.InspectionID FROM Inspections CROSS JOIN Violations"

mycursor.execute("SELECT Facilities.*, Inspections.*, Violations.* " \
                "FROM Facilities " \
                "   JOIN Inspections " \
                "       ON Inspections.FacilityID = Facilities.FacilityID " \
                "   JOIN Violations " \
                "       ON Violations.InspectionID = Inspections.InspectionID ")

myresult = mycursor.fetchall();
for x in myresult:
    print(x)

'''print("Facilities datatable: ")
mycursor.execute("SELECT * FROM Facilities")
my_result = mycursor.fetchall()
for x in my_result:
    print(x)
print()

print("Inspections datatable: ")
mycursor.execute("SELECT * FROM Inspections")
my_result = mycursor.fetchall()
for x in my_result:
    print(x)
    y = list(x)
    name = str(x[1])
    query = "SELECT facility_name FROM Facilities WHERE FacilityID = %s"
    mycursor.execute(query, name)
    y[1] = mycursor.fetchone()[0]
    print(tuple(y))
print()

print("Violations datatable: ")
mycursor.execute("SELECT * FROM Violations")
my_result = mycursor.fetchall()
for x in my_result:
    print(x)
print()'''

''' My original SQL schema: Create one large data table, where each row represents information about a specific health
inspection at a particular health facility, and columns label information about the facility, the inspection itself and violations
associated with that facility'''

'''mycursor.execute("DROP TABLE health_inspections");
mycursor.execute("CREATE TABLE health_inspections (id INT AUTO_INCREMENT PRIMARY KEY)");
mycursor.execute("ALTER TABLE health_inspections ADD COLUMN facility_name VARCHAR(255) NOT NULL");
mycursor.execute("ALTER TABLE health_inspections ADD COLUMN street_address VARCHAR(255) NOT NULL");
mycursor.execute("ALTER TABLE health_inspections ADD COLUMN city VARCHAR(255) NOT NULL");
mycursor.execute("ALTER TABLE health_inspections ADD COLUMN state VARCHAR(5) NOT NULL");
mycursor.execute("ALTER TABLE health_inspections ADD COLUMN zip_code VARCHAR(10) NOT NULL");
mycursor.execute("ALTER TABLE health_inspections ADD COLUMN inspection_date VARCHAR(255) NOT NULL");
mycursor.execute("ALTER TABLE health_inspections ADD COLUMN inspection_grade VARCHAR(10) NOT NULL");
mycursor.execute("ALTER TABLE health_inspections ADD COLUMN inspection_type VARCHAR(255) NOT NULL");
mycursor.execute("ALTER TABLE health_inspections ADD COLUMN violations VARCHAR(1000) NOT NULL");

sql = "INSERT INTO health_inspections (facility_name, street_address, city, state, zip_code, " \
      "inspection_date, inspection_grade, inspection_type, violations) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

with open('inspection_info.txt', 'r') as filehandle:
    inspections = json.load(filehandle)

val = []
for inspection in inspections:
    inspection_data = list(inspection.values())[0:8] # this should give something in the format (facility_name, address, city, zip_code, date, grade, violations)
    violations = list(inspection.values())[8]    # this is a dictionary
    inspection_data.append(str(violations))
    val.append(tuple(inspection_data))

mycursor.executemany(sql, val)
mydb.commit()  # this statement is required to make changes to the table

mycursor.execute("SELECT * FROM health_inspections")

my_result = mycursor.fetchall()

for x in my_result:
  print(x)'''
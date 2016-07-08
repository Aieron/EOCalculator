import globs


def main():
    allrows = ''
    globs.DBSOURCE = 'gdocs'
    if globs.DBSOURCE == 'local':
        import shelve
        import csv
        allrows = shelve.open('drows.db')
        with open('sample.csv', newline='') as f:
            reader = csv.reader(f)
            for globs.lastrow, row in enumerate(reader):
                allrows[str(globs.lastrow)] = row
        allrows.close()
        allrows = shelve.open('drows.db')
        for rowkey in allrows:
            print(allrows[rowkey])
    elif globs.DBSOURCE == 'gdocs':
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('Google Credentials.json', scope)
        gc = gspread.authorize(credentials)
        wks = gc.open_by_key('1qlgeGmj3ES6Sf_iIXuUJQURl9HoQ5sVlpN_VO_FH1Gs').sheet1
        for globs.lastrow in range(1, wks.row_count):
            arow = wks.row_values(globs.lastrow)
            if arow != ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
                        '', '']:
                print(str(arow))
            else:
                break
    else:
        pass

    # print(allrows)
    # print(globs.lastrow)

    return
'''
    fargs = {}
    for item in allrows['0']:
        fname = allrows['0'][item]
        if fname in globals():
            fargs[fname] = {}
            from inspect import _empty, signature
            sig = signature(eval(fname))
            # print("%s is a function with arguments %s" % (fname, sig))
            for param in sig.parameters.values():
                pname = param.name
                pdefault = param.default
                if pdefault is _empty:
                    fargs[fname][pname] = None
                    # print ('Required parameter: %s %s' % (fname, pname))
                else:
                    fargs[fname][pname] = pdefault
                    # print('I have default value for: %s %s %s' % (fname, pname, pdefault))
    # print(fargs)
'''

'''for item in allrows:
    if item != '0':
        print("%s: %s" % (item, allrows[item]))
        pass
'''

def delrow(allrows, rowkey):
    try:
        del allrows[rowkey]
    except:
        pass


def knights():
    return "Hi, I'm a knight."


def go(job, play = '', status = 'Okay'):
    return "I'm go."

if __name__ == "__main__":
    main()


"""
def calculator(row_number: int, column_number: int, character_level: int) -> int:
    base_level = int(worksheet.cell(row_number, (column_number + 2)).value)
    base_eppd = int(worksheet.cell(row_number, (column_number + 3)).value)
    monster_divinity = worksheet.cell(row_number, (column_number + 1)).value
    ksb = int(worksheet.cell(row_number, (column_number + 4)).value)
    effective_eppd = str((base_eppd + (base_eppd * ((base_level - character_level) / 10))))
    return print("%s is %s divinity with an EPPD of %s and KSB of %s"
                 % (monster, monster_divinity, effective_eppd, ksb))


def calcdivinity(row_number: int, column_number: int) -> int:
    mob_name = worksheet.cell(row_number, (column_number - 1)).value
    mob_divinity = worksheet.cell(row_number, column_number).value
    return print("%s is %s divinity" % (mob_name, mob_divinity))


def getmonstername():
    name = input("Enter the monster name: ")
    list_of_monsters = sorted(list(filter(None, worksheet.col_values(1))), key=str.lower)
    while name not in list_of_monsters:
        name = input("Enter a correct monster name: ")
    return name


def getcharacter():
    level = int(input("Enter your character level: "))
    while 0 >= level >= 25:
        level = int(input("Enter your real character level: "))
    return level


def getdivinity():
    divinity = input("Enter your divinity: ")
    list_of_divinities = sorted(list(filter(None, worksheet.col_values(2))), key=str.lower)
    while divinity not in list_of_divinities:
        divinity = input("Enter a correct divinity: ")
    return divinity


startinput = input("Monster or divinity search? ")

while startinput != "Monster" and startinput != "Divinity":
    startinput = input("Enter 'Monster' or 'Divinity' to proceed: ")

if startinput == "Monster":
    monster = getmonstername()
    characterlevel = getcharacter()
    monster_to_compare = worksheet.find(monster)
    rownumber = monster_to_compare.row
    columnnumber = monster_to_compare.col
    eppd = calculator(rownumber, columnnumber, characterlevel)
elif startinput == "Divinity":
    character_divinity = getdivinity()
    characterlevel = getcharacter()

    if character_divinity == "Fire":
        character_divinity = "Night"
    elif character_divinity == "Night":
        character_divinity = "Earth"
    elif character_divinity == "Earth":
        character_divinity = "Lightning"
    elif character_divinity == "Lightning":
        character_divinity = "Ice"
    elif character_divinity == "Ice":
        character_divinity = "Fire"
    else:
        print("Error: Divinity invalid.")

    divinity_to_compare = worksheet.find(character_divinity)
    rownumber = divinity_to_compare.row
    columnnumber = divinity_to_compare.col
    mobdivinity = calcdivinity(rownumber, columnnumber)"""

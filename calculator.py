import globs
from flask import Flask, request, render_template
from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField
from wtforms.validators import DataRequired, Optional

app = Flask(__name__)


class RequiredIf(object):
    """Validates field conditionally.
    Usage::
        login_method = StringField('', [AnyOf(['email', 'facebook'])])
        email = StringField('', [RequiredIf(login_method='email')])
        password = StringField('', [RequiredIf(login_method='email')])
        facebook_token = StringField('', [RequiredIf(login_method='facebook')])
    """
    def __init__(self, *args, **kwargs):
        self.conditions = kwargs

    def __call__(self, form, field):
        for name, data in self.conditions.items():
            if name not in form._fields:
                Optional(form, field)
            else:
                condition_field = form._fields.get(name)
                if condition_field.data == data and not field.data:
                    DataRequired()(form, field)
        Optional()(form, field)


class CalcForm(Form):
    gkey = StringField('Your Google Spreadsheet Key', [RequiredIf(csvfile='')])
    csvfile = FileField('Your CSV file', [RequiredIf(gkey='')])


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in globs.ALLOWED_EXTENSIONS


@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == "POST":
        form = CalcForm(csrf_enabled=False)
        if form.validate_on_submit():
            if form.gkey.data:
                globs.GKEY = form.gkey.data
                calculator('gdocs')
                return "I processed Google Spreadsheet."
            if form.csvfile.data:
                import os
                from werkzeug import secure_filename
                app.config['UPLOAD_FOLDER'] = globs.UPLOAD_FOLDER
                file = request.files['csvfile']
                if file and allowed_file(file.filename):
                    globs.FILE = secure_filename(file.filename)
                    file.save(os.path.join(globs.UPLOAD_FOLDER, globs.FILE))
                calculator('local')
                return "I processed an uploaded CSV file."
        return render_template('calculator.html', form=form)
    else:
        form = CalcForm(csrf_enabled=False)
        return render_template('calculator.html', form=form)


def calculator(dbsource):
    """Allow processing of multiple worksheets.

    During testing, main is set to process one Google Spreadsheet and one local
    csv file. It also creates a list of global functions and translates them via
    translation table to their lower-case versions for recognizing function names
    in column labels. A Pythonic switch statement calls dbgdocs once and dblocal
    once."""
    funcs = [x for x in globals().keys() if x[:2] != '__']  # List all functions
    globs.funcslc = [x.lower() for x in funcs]  # Set all function names to lower case
    globs.transfuncs = dict(zip(globs.funcslc, funcs))  # Keep case translation table
    dbmethod = {"local": dblocal, "gdocs": dbgdocs}
    dbmethod[dbsource]()


def dblocal():
    """Loads a local csv file and dumps it into a shelve object for processing.

    While support for csv files will be very useful for many people, using the
    shelve API here is to leave a hook for the external shove library which will
    allow this to run on larger datasets by connecting it to other mainstream
    database services."""
    import shelve, csv, os
    allrows = shelve.open('drows.db')
    with open(os.path.join(globs.UPLOAD_FOLDER, globs.FILE), newline='') as f:
        reader = csv.reader(f)
        for rowdex, arow in enumerate(reader):  # Dump entire csv into shelve.
            allrows[str(rowdex + 1)] = arow
    allrows.close()
    allrows = shelve.open('drows.db')
    for rowkey in sorted(allrows):  # Process each row (list) from the shelve
        newrow = processrow(rowkey, allrows[rowkey])
        allrows[rowkey] = newrow
    with open('sample.csv', 'w', newline='') as f:
        w = csv.writer(f)
        for rowkey in sorted(allrows):
            w.writerow(allrows[rowkey])


def dbgdocs():
    """Keeps a Google Spreadsheet open for row-by-row processing.

    While Google Spreadsheets is not the most efficient or scalable way to manage
    this process. It provides a ready-made user interface for convenient
    interactive sessions with smaller datasets. Demonstrating this approach to
    people is impressive and has compelling charm."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('Creds.json', scope)
    gc = gspread.authorize(credentials)
    wks = gc.open_by_key(globs.GKEY).sheet1
    for rowdex in range(1, wks.row_count):  # Start stepping through every row.
        arow = wks.row_values(rowdex)
        if arow != ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
                    '', '']:  # Only processes it if it does not come back as an empty list.
            newrow = processrow(str(rowdex), arow)  # Replace question marks in row
            for coldex, acell in enumerate(newrow):  # Then step through new row
                if questionmark(arow, rowdex, coldex, acell):  # Update Google worksheet
                    wks.update_cell(rowdex, coldex+1, acell)  # Gspread starts at column 1
        else:
            break  # Stop grabbing new rows at the first empty row encountered.


def questionmark(oldrow, rowdex, coldex, acell):
    """Returns true if a question mark is supposed to be replaced in a cel.

    This is called for every cell on every row processed and checks whether
    question mark replacement should actually occur."""
    if acell != '':
        if rowdex != 1:
            if globs.row1[coldex] in globs.funcslc:
                if oldrow[coldex] == '?':
                    return True
    return False


def processrow(rowdex, arow):
    changedrow = arow[:]
    if str(rowdex) == '1':
        globs.row1 = [x.lower() for x in changedrow]
        row1funcs(changedrow)
    else:
        for coldex, acell in enumerate(changedrow):
            if questionmark(arow, rowdex, coldex, acell):
                changedrow[coldex] = evalfunc(coldex, changedrow)
    return changedrow


def evalfunc(coldex, arow):
    fname = globs.transfuncs[globs.row1[coldex]]
    fargs = globs.fargs[coldex]
    evalme = "%s(" % fname
    if fargs:
        for anarg in fargs:
            anarg = anarg.lower()
            argval = getargval(anarg, fargs[anarg], arow)
            evalme = "%s%s=%s, " % (evalme, anarg, argval)
        evalme = evalme[:-2] + ")"
    else:
        evalme += ')'
    # return '%s: %s' % (evalme, eval(evalme))
    return eval(evalme)


def getargval(anarg, defargval, arow):
    for coldex, acol in enumerate(globs.row1):
        if acol == anarg:
            if arow[coldex]:
                return adq(arow[coldex])
    if defargval:
        return adq(defargval)
    else:
        return 'foo'


def adq(aval):
    if aval is None:
        return None
    else:
        return "'%s'" % aval


def row1funcs(arow):
    fargs = {}
    for coldex, fname in enumerate(arow):
        if fname.lower() in globs.funcslc:
            fargs[coldex] = {}
            from inspect import _empty, signature
            sig = signature(eval(fname))
            for param in sig.parameters.values():
                pname = param.name
                pdefault = param.default
                if pdefault is _empty:
                    fargs[coldex][pname] = None
                else:
                    fargs[coldex][pname] = pdefault
    globs.fargs = fargs


def Func1():
    return "Out from func1"


def Func2(param1, param2='', status = 'Okay'):
    return "%s %s" % (param1, param2)

# if __name__ == "__main__":
#    main()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

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

import os, sys, inspect, webbrowser, base64
import re
import dash
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State, ALL
import pandas as pd
from mysql.connector import Error
from threading import Timer
import dash_daq as daq
import dash_bootstrap_components as dbc
from src import config
from src import db_connection
from datetime import datetime, date
from src.config import Config
from src.db_connection import DBConnector


""" Connect to MySQL database """
CONGIF = config.Config.dbinfo().copy()
CONN = db_connection.DBConnector(CONGIF['user'],CONGIF['password'],CONGIF['database'])
mydb = CONN.cnx
cursor = CONN.cursor

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "JauntyJalopies"
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

def get_total_number_of_avaliable_vehicles():
    sql = "SELECT COUNT(VIN) FROM Vehicle WHERE Sold_date IS NULL"
    output = CONN.simple_query(sql)[0][0]
    return str(output)

def get_vehicle_type():
    options = [
        {"label": "Car", "value":"Car"},
        {"label": "Convertible", "value":"Convertible"},
        {"label": "SUV", "value":"SUV"},
        {"label":"Truck", "value":"Truck"},
        {"label":"VanMinivan", "value":"VanMinivan"}
    ]
    return options

def get_vehicle_manufacturer():
    sql = "SELECT Manufacturer_name FROM Manufacturer"
    output = CONN.simple_query(sql)
    res = []
    for each_brand in output:
        res.append(each_brand[0])
    return pd.DataFrame({'vm':res})

def get_model_year():
    return int(datetime.now().year) + 1

def get_vehicle_color():
    sql = "SELECT Color FROM VehicleColor"
    output = CONN.simple_query(sql)
    res = []
    for each_color in output:
        res.append(each_color[0])
    return pd.DataFrame({'vc':res})

def get_vin():
    sql = "SELECT VIN FROM Vehicle WHERE Sold_date is NULL"
    output = CONN.simple_query(sql)
    res = []
    for each in output:
        res.append(each[0])
    return pd.DataFrame({'vin':res})

def get_all_vin():
    sql = "SELECT VIN FROM Vehicle"
    output = CONN.simple_query(sql)
    res = []
    for each in output:
        res.append(each[0])
    return pd.DataFrame({'vin':res})

def get_vehicle(vin):
    sql = "SELECT * FROM Vehicle WHERE VIN = %s"
    val = (vin,)
    output = CONN.query(sql, val)
    res = []
    for val in output[0]:
        res.append(str(val))
    return res

def get_colors(vin):
    sql = "SELECT Color FROM VehicleColor WHERE VIN = %s"
    val = (vin,)
    output = CONN.query(sql, val)
    res = []
    for val in output:
        res.append(str(val[0]))
    return res

def get_Add_date():
    return datetime.today().strftime("%Y-%m-%d")

def call_get_type_details_method(type, vin):
    if type == 'Car':
        return get_Car(vin)
    if type == 'Convertible':
        return get_Convertible(vin)
    if type == 'SUV':
        return get_SUV(vin)
    if type == 'VanMinivan':
        return get_VanMinivan(vin)
    if type == 'Truck':
        return get_Truck(vin)

def get_Car(vin):
    sql = "SELECT Num_of_doors FROM Car WHERE VIN = %s"
    val = (vin,)
    output = CONN.query(sql, val)
    res = []
    if not output:
        return res
    for val in output[0]:
        res.append(str(val))
    return res

def get_Convertible(vin):
    sql = "SELECT Roof_type, Back_seat_count FROM Convertible WHERE VIN = %s"
    val = (vin,)
    output = CONN.query(sql, val)
    res = []
    if not output:
        return res
    for val in output[0]:
        res.append(str(val))
    return res

def get_SUV(vin):
    sql = "SELECT Drivetrain_type, Num_of_cupholders FROM SUV WHERE VIN = %s"
    val = (vin,)
    output = CONN.query(sql, val)
    res = []
    if not output:
        return res
    for val in output[0]:
        res.append(str(val))
    return res

def get_VanMinivan(vin):
    sql = "SELECT Has_back_door FROM VanMinivan WHERE VIN = %s"
    val = (vin,)
    output = CONN.query(sql, val)
    res = []
    if not output:
        return res
    for val in output[0]:
        res.append(str(val))
    return res

def get_Truck(vin):
    sql = "SELECT Cargo_capacity, Num_of_rear_axies, Cargo_cover_type FROM Truck WHERE VIN = %s"
    val = (vin,)
    output = CONN.query(sql, val)
    res = []
    if not output:
        return res
    for val in output[0]:
        res.append(str(val))
    return res


def get_password(uname):
    query = "SELECT Password FROM User WHERE Username='%s'" % uname
    df = pd.read_sql(query, mydb)
    li = df.to_dict('records')
    passw = li[0]["Password"]
    return passw


def get_logged_in_admin(uname):
    passw = get_password(uname)
    logged_in_owner = html.Div([
        dcc.Link(html.Button('Log Out'), href='/'),
        html.H1(children="Hi, Roland! Welcome to the Jaunty Jalopies Service Writer Portal!"),
        html.Br(),
        html.Div(dcc.Link(html.Button('Inventory Clerk'), href='/logged_in_inventory_clerk/%s/%s' % (uname, passw), refresh=True)),
        html.Br(), html.Br(),
        html.Div(dcc.Link(html.Button('Service Writer'), href='/logged_in_service_writer/' + uname, refresh=True)),
        html.Br(), html.Br(),
        html.Div(dcc.Link(html.Button('Sales Person'), href='/logged_in_sales/' + uname, refresh=True)),
        html.Br(), html.Br(),
        html.Div(dcc.Link(html.Button('Manager'), href='/logged_in_manager/' + uname, refresh=True)),
        html.Br(), html.Br(),
    ])
    return logged_in_owner


def layout_vehicle_details(vinnum, role, uname):
    vehicle_values = get_vehicle(vinnum)
    input_vehicle_values = {
    'VIN': "",
    'manufacturer': "",
    'model_name': "",
    'model_year': "",
    'invoice_price': "",
    'description': "",
    'customerID': "",
    'sold_date': "",
    'sold_price': "",
    'add_date': str(get_Add_date()),
    'vehicle_type': "",
    'soldby': "",
    'addby': ""
    }
    select_colors = {'colors': []}
    for i, k in enumerate(input_vehicle_values.keys()):
        input_vehicle_values[k] = vehicle_values[i]

    select_colors['colors'] = get_colors(vinnum)
    colors = ""
    n = len(select_colors['colors'])
    for i, c in enumerate(select_colors['colors']):
        if i < n - 1:
            colors += (c + ", ")
    colors += select_colors['colors'][n - 1]
    show_type = input_vehicle_values['vehicle_type']
    type_details = call_get_type_details_method(show_type, vinnum)

    vehicle_type_details_layout = ""
    if len(type_details) != 0:
        if show_type == "Car":
            vehicle_type_details_layout = html.Div(["Number of doors: " + type_details[0]])
        elif show_type == 'Convertible':
            vehicle_type_details_layout = html.Div([html.Div(["Roof type: " + type_details[0]]),
                                    html.Div(["Back seat count: " + type_details[1]])])
        elif show_type == 'SUV':
            vehicle_type_details_layout = html.Div([html.Div(["Drivetrain type: " + type_details[0]]),
                             html.Div(["Number of cupholders: " + type_details[1]])])
        elif show_type == 'VanMinivan':
            vehicle_type_details_layout = html.Div(["Has Driver’s Side Back Door: " + type_details[0]])
        elif show_type =='Truck':
            vehicle_type_details_layout = html.Div([html.Div(["Cargo capacity: " + type_details[0]]),
                          html.Div(["Number of rear axles: " + type_details[1]]),
                          html.Div(["Cargo cover type: " + type_details[2]])])
    if role == "Sales":
        vehicle_details_layout = html.Div([
            html.Div([dcc.Link(html.Button('Log Out'), href='/'),
            dcc.Link(html.Button('Return to Sales Main Page'), href='/logged_in_sales/' + uname),
            html.H1("Welcome to the Jaunty Jalopies Sales Portal!")]),
            html.Br(),
            html.H3("Detail for Vehicle " + vinnum + ":"),
            html.Br(),
            html.Div('VIN: ' + input_vehicle_values['VIN']),
            html.Div('Manufacturer: ' + input_vehicle_values['manufacturer']),
            html.Div('Model Name: ' + input_vehicle_values['model_name']),
            html.Div('Model Year: ' + input_vehicle_values['model_year']),
            html.Div('List Price: %s' % str("{:.2f}".format(1.25 * float(input_vehicle_values['invoice_price'])))),
            html.Div('Description: ' + input_vehicle_values['description']),
            html.Div('Color(s): ' + colors),
            html.Div('Vehicle Type: ' + input_vehicle_values['vehicle_type']),
            html.Div(vehicle_type_details_layout),
            html.Br(),
            html.Br(),
            html.Div([dcc.Link(html.Button('Sell This Vehicle'), href='/logged_in_sales/' + uname + '/view_vehicle_detail/' + vinnum + '/sell')])
            ])
    elif role == "Inventory":
        query = "SELECT Password FROM User WHERE Username='%s'" % uname
        df = pd.read_sql(query, mydb)
        li = df.to_dict('records')
        passw = li[0]["Password"]
        vehicle_details_layout = html.Div(id='add-vehicl-detaial', children=[
            dcc.Link(html.Button('Return to Inventory Clerk Main Page'), href='/logged_in_inventory_clerk/%s/%s' % (uname, passw)),
            html.H1("Welcome to the Jaunty Jalopies Inventory Clerk Portal!"),
            html.Br(),
            html.H3('Added Vehicle Details:'),
            html.Hr(), html.Br(),
            html.Div('VIN: ' + input_vehicle_values['VIN']),
            html.Div('Vehicle Type: ' + input_vehicle_values['vehicle_type']),
            html.Div('Model Year: ' + input_vehicle_values['model_year']),
            html.Div('Manufacturer: %s' % input_vehicle_values['manufacturer']),
            html.Div('Model Name: ' + input_vehicle_values['model_name']),
            html.Div('Color(s): ' + colors),
            html.Div('Invoice Price: %s' % str("{:.2f}".format(float(input_vehicle_values['invoice_price'])))),
            html.Div('List Price: %s' % str("{:.2f}".format(1.25 * float(input_vehicle_values['invoice_price'])))),
            html.Div('Description: %s' % (input_vehicle_values['description'] if input_vehicle_values['description'] != "" else "None")),
            html.Div(vehicle_type_details_layout),
            dcc.ConfirmDialog(id='confirm-add-vehicle-dialog',
                              message='This is to confirm you\'ve added this vehicle successfully! Click any button to return to inventory clerk main page!',
                              displayed=False),
            html.Div(id='add-vehicle-detail-placeholder')
        ])
    elif role == "Manager":
        icquery = "SELECT Fname, Lname FROM User WHERE Username=%s"
        icval = (input_vehicle_values['addby'],)
        df = CONN.query(icquery, icval)
        li = []
        for val in df[0]:
                li.append(str(val))
        inventoryclerk = li[0] + " " + li[1]
        if input_vehicle_values['sold_date'] == "None":
            vehicle_sell_info = html.H3("This vehicle has not been sold yet.")
        else:
            cquery = "SELECT CustomerID, Email, Street, City, State, Zipcode, Phone_number FROM Customer WHERE CustomerID=%s"
            cval = (input_vehicle_values['customerID'],)
            dfc = CONN.query(cquery, cval)
            lic = []
            for val in dfc[0]:
                lic.append(str(val))
            spquery = "SELECT Fname, Lname FROM User WHERE Username=%s"
            spval = (input_vehicle_values['soldby'],)
            dfsp = CONN.query(spquery, spval)
            lisp = []
            for val in dfsp[0]:
                lisp.append(str(val))
            bquery = "SELECT Tax_ID, Title, Business_name, Fname, Lname, CustomerID FROM Business WHERE CustomerID=%s"
            bval = (input_vehicle_values['customerID'],)
            dfb = CONN.query(bquery, bval)
            if dfb == []:
                ipquery = "SELECT Fname, Lname FROM IndividualPerson WHERE CustomerID=%s"
                ipval = (input_vehicle_values['customerID'],)
                dfip = CONN.query(ipquery, ipval)
                liip = []
                for val in dfip[0]:
                    liip.append(str(val))
                vehicle_sell_info = html.Div([html.H3("Customer info who purchased this vehicle:"),
                                    html.Div('CustomerID: ' + lic[0]),
                                    html.Div('Email: ' + lic[1]),
                                    html.Div('Address: ' + lic[2] + ', ' + lic[3] + ', ' + lic[4] + ', ' + lic[5]),
                                    html.Div('Phone Number: ' + lic[6]),
                                    html.Div('Name: ' + liip[0] + ' ' + liip[1]),
                                    html.Div('List Price: %s' % str("{:.2f}".format(1.25 * float(input_vehicle_values['invoice_price'])))),
                                    html.Div('Sold Price: ' + input_vehicle_values['sold_price']),
                                    html.Div('Sold Date: ' + input_vehicle_values['sold_date']),
                                    html.Div('Sold By Sales Person: ' + lisp[0] + ' ' + lisp[1]),
                                    ])
            else:
                lib = []
                for val in dfb[0]:
                    lib.append(str(val))
                vehicle_sell_info = html.Div([html.H3("Customer info who purchased this vehicle:"),
                                    html.Div('CustomerID: ' + lic[0]),
                                    html.Div('Email: ' + lic[1]),
                                    html.Div('Address: ' + lic[2] + ', ' + lic[3] + ', ' + lic[4] + ', ' + lic[5]),
                                    html.Div('Phone Number: ' + lic[6]),
                                    html.Div('Title: ' + lib[1]),
                                    html.Div('Business Name: ' + lib[2]),
                                    html.Div('Name: ' + lib[3] + ' ' + lib[4]),
                                    html.Div('List Price: %s' % str("{:.2f}".format(1.25 * float(input_vehicle_values['invoice_price'])))),
                                    html.Div('Sold Price: ' + input_vehicle_values['sold_price']),
                                    html.Div('Sold Date: ' + input_vehicle_values['sold_date']),
                                    html.Div('Sold By Sales Person: ' + lisp[0] + ' ' + lisp[1]),
                                    ])
        rquery = "SELECT VIN, CustomerID, Start_date, Labor_fee, Description, Complete_date, Odometer, Username FROM Repair WHERE VIN=%s"
        rval = (vinnum,)
        dfr = CONN.query(rquery, rval)
        if dfr == []:
            vehicle_repair_info = html.H3("This vehicle doesn't have any repair.")
        else:
            rsql = "(SELECT CONCAT(ip.Fname, ' ', ip.Lname) AS Customer_name, CONCAT(u.Fname, ' ', u.Lname) AS Service_writer_name,\
r.Start_date, r.Complete_date, r.Labor_fee, IFNULL(ROUND(SUM(p.Part_price * p.Quantity), 2), 0) AS Parts_cost,\
ROUND((r.Labor_fee + IFNULL(SUM(p.Part_price * p.Quantity), 0)),2) AS Total_cost \
FROM cs6400_fa21_team020.Repair AS r \
join cs6400_fa21_team020.Customer AS c ON r.CustomerID = c.CustomerID \
join cs6400_fa21_team020.IndividualPerson AS ip ON c.CustomerID = ip.CustomerID \
join cs6400_fa21_team020.User AS u ON r.Username = u.Username \
left join cs6400_fa21_team020.Part AS p ON r.VIN = p.VIN AND r.CustomerID = p.CustomerID AND r.Start_date = p.Start_date \
WHERE r.VIN=%s \
GROUP BY r.VIN, r.CustomerID, r.Start_date, ip.Fname, ip.Lname) \
UNION ALL \
(SELECT b.Business_name AS Customer_name, CONCAT(u.Fname, ' ', u.Lname) AS Service_writer_name, \
r.Start_date, r.Complete_date, r.Labor_fee, IFNULL(ROUND(SUM(p.Part_price * p.Quantity), 2), 0) AS Parts_cost, \
ROUND((r.Labor_fee + IFNULL(SUM(p.Part_price * p.Quantity),0)),2) AS Total_cost \
FROM cs6400_fa21_team020.Repair AS r \
join cs6400_fa21_team020.Customer AS c ON r.CustomerID = c.CustomerID \
join cs6400_fa21_team020.Business AS b ON c.CustomerID = b.CustomerID \
join cs6400_fa21_team020.User AS u ON r.Username = u.Username \
left join cs6400_fa21_team020.Part AS p ON r.VIN = p.VIN AND r.CustomerID = p.CustomerID AND r.Start_date = p.Start_date \
WHERE r.VIN=%s \
GROUP BY r.VIN, r.CustomerID, r.Start_date, b.Business_name)"
            repairval = (vinnum, vinnum,)
            output = CONN.query(rsql, repairval)
            repairdf = pd.DataFrame(output, columns=["Customer Name", "Service Writer Name", "Start Date", "Complete Date", "Labor Fee", "Parts Cost", "Total Cost"])
            vehicle_repair_info = html.Div([html.H3("Repairs:"),
                                            html.Table(children=[
                                            dbc.Container([
                                            html.Br(),
                                            dash_table.DataTable(
                                                id='manager_view_repair_table',
                                                columns=[{"name": i, "id": i} for i in repairdf.columns],
                                                data=repairdf.to_dict('results'),
                                                column_selectable="single",),])])])
        vehicle_details_layout = html.Div([
            html.Div([dcc.Link(html.Button('Log Out'), href='/'),
            dcc.Link(html.Button('Return to Manager Main Page'), href='/logged_in_manager'),
            html.H1("Welcome to the Jaunty Jalopies Manager Portal!")]),
            html.Br(),
            html.H3("Detail for Vehicle " + vinnum + ":"),
            html.Br(),
            html.Div('VIN: ' + input_vehicle_values['VIN']),
            html.Div('Manufacturer: ' + input_vehicle_values['manufacturer']),
            html.Div('Model Name: ' + input_vehicle_values['model_name']),
            html.Div('Model Year: ' + input_vehicle_values['model_year']),
            html.Div('Invoice Price: %s' % str("{:.2f}".format(float(input_vehicle_values['invoice_price'])))),
            html.Div('Description: ' + input_vehicle_values['description']),
            html.Div('Color(s): ' + colors),
            html.Div('Vehicle Type: ' + input_vehicle_values['vehicle_type']),
            html.Div(vehicle_type_details_layout),
            html.Div('Vehicle Added Date: ' + input_vehicle_values['add_date']),
            html.Div('Vehicle Added By Inventory Clerk: ' + inventoryclerk),
            html.Br(),
            html.Div(vehicle_sell_info),
            html.Br(),
            html.Div(vehicle_repair_info),
            html.Br(),
            ])
    elif role == "Anonymous":
        vehicle_details_layout = html.Div([
            html.Div([dcc.Link(html.Button('Return to Main Page'), href='/'),
            html.H1("Welcome to the Jaunty Jalopies Portal!")]),
            html.Br(),
            html.H3("Detail for Vehicle " + vinnum + ":"),
            html.Br(),
            html.Div('VIN: ' + input_vehicle_values['VIN']),
            html.Div('Manufacturer: ' + input_vehicle_values['manufacturer']),
            html.Div('Model Name: ' + input_vehicle_values['model_name']),
            html.Div('Model Year: ' + input_vehicle_values['model_year']),
            html.Div('List Price: %s' % str("{:.2f}".format(1.25 * float(input_vehicle_values['invoice_price'])))),
            html.Div('Description: ' + input_vehicle_values['description']),
            html.Div('Color(s): ' + colors),
            html.Div('Vehicle Type: ' + input_vehicle_values['vehicle_type']),
            html.Div(vehicle_type_details_layout)
            ])
    return vehicle_details_layout


@app.callback(Output('confirm-add-vehicle-dialog', 'displayed'),
Input('add-vehicl-detaial', 'children'))
def confirm_added_vehicle(content):
    if content != "":
        return True
    else:
        return False


@app.callback(Output('add-vehicle-detail-placeholder', 'children'),
[Input('confirm-add-vehicle-dialog', 'submit_n_clicks'),
Input('confirm-add-vehicle-dialog', 'cancel_n_clicks')],
State('url', 'pathname'))
def return_to_inventory_clerk_main(snc, cnc, pathname):
    uname = pathname.split('/')[-2] 
    passw = pathname.split('/')[-1]
    if snc or cnc:
        return dcc.Location(id='return-inventory-clerk-main', href='/logged_in_inventory_clerk/%s/%s' % (uname, passw))


def layout_sales_add_individual_customer(vin, uname, driverlicense):
    sales_add_individual_customer_layout = html.Div([
        html.Div([dcc.Link(html.Button('Log Out'), href='/'),
            dcc.Link(html.Button('Return to Sales Main Page'), href='/logged_in_sales/' + uname),
            html.H1("Welcome to the Jaunty Jalopies Sales Portal!")]),
        html.H3("Please enter the detail information to add this customer!"),
        html.Div(children=[
                    html.Label('Driver License Number: '),
                    html.Label(driverlicense),
                    html.Br(),
                    html.Label('First Name: '),
                    dcc.Input(id='Fname_i', value='', type='text'),
                    html.Br(),
                    html.Label('Last Name: '),
                    dcc.Input(id='Lname_i', value='', type='text'),
                    html.Br(),
                    html.Label('Email: '),
                    dcc.Input(id='email_i', value='', type='email'),        
                    html.Br(),
                    html.Label('Street: '),
                    dcc.Input(id='street_i', value='', type='text'),
                    html.Br(),
                    html.Label('City: '),
                    dcc.Input(id='city_i', value='', type='text'),
                    html.Br(),
                    html.Label('State: '),
                    dcc.Input(id='state_i', value='', type='text'),
                    html.Br(),
                    html.Label('Zipcode: '),
                    dcc.Input(id='zipcode_i', value='', type='number'),
                    html.Br(),
                    html.Label('Phone: '),
                    dcc.Input(id='phone_i', value='', type='number'),
                ], style={'padding': 50, 'font-size':'16px'}),
            dcc.Link(html.Button("Cancel"), id='btn-return_i', href='/logged_in_sales/' + uname + '/view_vehicle_detail/' + vin + '/sell', refresh=True),
            html.Button('Save', id='btn-save_i', n_clicks=0),
            html.Div(id='add-success_i'),
            html.Div(id='return_to_sales_order_form_i')])
    return sales_add_individual_customer_layout

@app.callback(
    Output('add-success_i', 'children'),
    Input("btn-save_i", "n_clicks"),
    State("Fname_i", "value"), 
    State("Lname_i", "value"), 
    State("email_i", "value"), 
    State("street_i", "value"), 
    State("city_i", "value"), 
    State("state_i", "value"), 
    State("zipcode_i", "value"), 
    State("phone_i", "value"), 
    State("url", "pathname"),
)

def add_individual_customer(n_clicks, Fname_i, Lname_i, email_i, street_i, city_i, state_i, zipcode_i, phone_i, pathname):
    driverlicense = pathname.split('/')[-1]
    driverlicense = driverlicense.replace("add_individual_customer_", "")
    if n_clicks > 0:
        if Fname_i == "" or Lname_i == "":
            return html.Div(children='Customer name can\'t be empty!')
        if street_i == "" or city_i == "" or state_i == "":
            return html.Div(children='Customer address can\'t be empty!')
        if len(str(zipcode_i)) != 5:
            return html.Div(children='Customer zipcode must have 5 digits!')
        if str(phone_i) == "":
            return html.Div(children='Customer phone number can\'t be empty!')
        query1="INSERT INTO Customer (Email, Street, City, State, Zipcode, Phone_number) VALUES('%s','%s','%s','%s','%s','%s')"%(email_i, street_i, city_i, state_i, zipcode_i, phone_i)
        query2="INSERT INTO IndividualPerson (ID, Fname, Lname, CustomerID) VALUES ('%s', '%s', '%s', LAST_INSERT_ID())"%(driverlicense, Fname_i, Lname_i)
        cursor.execute(query1)
        mydb.commit()
        cursor.execute(query2)
        mydb.commit()
        return html.Div([dcc.ConfirmDialog(id='confirm-add-dialog-i', message='You\'ve successfully added this customer! Click any button to return to the sales order!', displayed = True)])

@app.callback(dash.dependencies.Output('return_to_sales_order_form_i', 'children'),
[dash.dependencies.Input('confirm-add-dialog-i', 'submit_n_clicks'),
dash.dependencies.Input('confirm-add-dialog-i', 'cancel_n_clicks')],
State('url', 'pathname'))

def return_to_sales_main_i(snc, cnc, pathname):
    newpathname = pathname.split('/add_individual_customer')[0]
    if snc or cnc:
        return dcc.Location(href=newpathname, id='sales_order_page')

def layout_sales_add_business_customer(vin, uname, taxid):
    sales_add_business_customer_layout = html.Div([
        html.Div([dcc.Link(html.Button('Log Out'), href='/'),
            dcc.Link(html.Button('Return to Sales Main Page'), href='/logged_in_sales/' + uname),
            html.H1("Welcome to the Jaunty Jalopies Sales Portal!")]),
        html.H3("Please enter the detail information to add this customer!"),
        html.Div(children=[
                    html.Br(),
                    html.Label('Tax ID: '),
                    html.Label(taxid),
                    html.Br(),
                    html.Label('Title: '),
                    dcc.Input(id='title', value='', type='text'),
                    html.Br(),
                    html.Label('Business Name: '),
                    dcc.Input(id='businessname', value='', type='text'),
                    html.Br(),
                    html.Label('First Name: '),
                    dcc.Input(id='Fname_b', value='', type='text'),
                    html.Br(),
                    html.Label('Last Name: '),
                    dcc.Input(id='Lname_b', value='', type='text'),
                    html.Br(),
                    html.Label('Email: '),
                    dcc.Input(id='email_b', value='', type='email'),        
                    html.Br(),
                    html.Label('Street: '),
                    dcc.Input(id='street_b', value='', type='text'),
                    html.Br(),
                    html.Label('City: '),
                    dcc.Input(id='city_b', value='', type='text'),
                    html.Br(),
                    html.Label('State: '),
                    dcc.Input(id='state_b', value='', type='text'),
                    html.Br(),
                    html.Label('Zipcode: '),
                    dcc.Input(id='zipcode_b', value='', type='number'),
                    html.Br(),
                    html.Label('Phone: '),
                    dcc.Input(id='phone_b', value='', type='number'),
                ], style={'padding': 50, 'font-size':'16px'}),
                dcc.Link(html.Button("Cancel"), id='btn-return_b', href='/logged_in_sales/' + uname + '/view_vehicle_detail/' + vin + '/sell', refresh=True),
                html.Button('Save', id='btn-save_b', n_clicks=0),
                html.Div(id='add-success_b'),
                html.Div(id='return_to_sales_order_form_b')])
    return sales_add_business_customer_layout

@app.callback(
    Output('add-success_b', 'children'),
    Input("btn-save_b", "n_clicks"),
    State("title", "value"), 
    State("businessname", "value"), 
    State("Fname_b", "value"), 
    State("Lname_b", "value"), 
    State("email_b", "value"), 
    State("street_b", "value"), 
    State("city_b", "value"), 
    State("state_b", "value"), 
    State("zipcode_b", "value"), 
    State("phone_b", "value"), 
    State("url", "pathname"),
)

def add_business_customer(n_clicks, title, businessname, Fname_b, Lname_b, email_b, street_b, city_b, state_b, zipcode_b, phone_b, pathname):
    taxid = pathname.split('/')[-1]
    taxid = taxid.replace("add_business_customer_", "")
    newpathname = pathname.split('/add_business_customer')[0]
    if n_clicks > 0:
        if title == "":
            return html.Div(children='Title can\'t be empty!')
        if businessname == "":
            return html.Div(children='Business name can\'t be empty!')
        if Fname_b == "" or Lname_b == "":
            return html.Div(children='Customer name can\'t be empty!')
        if street_b == "" or city_b == "" or state_b == "":
            return html.Div(children='Customer address can\'t be empty!')
        if len(str(zipcode_b)) != 5:
            return html.Div(children='Customer zipcode must have 5 digits!')
        if str(phone_b) == "":
            return html.Div(children='Customer phone number can\'t be empty!')
        query1="INSERT INTO Customer (Email, Street, City, State, Zipcode, Phone_number) VALUES('%s','%s','%s','%s','%s','%s')"%(email_b, street_b, city_b, state_b, zipcode_b, phone_b)
        query2="INSERT INTO Business (Tax_ID, Title, Business_name, Fname, Lname, CustomerID) VALUES ('%s', '%s', '%s', '%s', '%s', LAST_INSERT_ID())"%(taxid, title, businessname, Fname_b, Lname_b)
        cursor.execute(query1)
        mydb.commit()
        cursor.execute(query2)
        mydb.commit()
        return html.Div([dcc.ConfirmDialog(id='confirm-add-dialog-b', message='You\'ve successfully added this customer! Click any button to return to the sales order!', displayed = True)])

@app.callback(dash.dependencies.Output('return_to_sales_order_form_b', 'children'),
[dash.dependencies.Input('confirm-add-dialog-b', 'submit_n_clicks'),
dash.dependencies.Input('confirm-add-dialog-b', 'cancel_n_clicks')],
State('url', 'pathname'))

def return_to_sales_main_b(snc, cnc, pathname):
    newpathname = pathname.split('/add_business_customer')[0]
    if snc or cnc:
        return dcc.Location(href=newpathname, id='sales_order_page_b')

def layout_sales_order_form(vinnum, uname):
    sales_order_form_layout = html.Div([
        html.Div([dcc.Link(html.Button('Log Out'), href='/'),
            dcc.Link(html.Button('Return to Sales Main Page'), href='/logged_in_sales/' + uname),
            html.H1("Welcome to the Jaunty Jalopies Sales Portal!")]),
        dcc.Tabs([
            dcc.Tab(label='Individual Person', children=[
                html.Br(),
                html.Div([html.Label('Individual ID',className="label"),
                    dcc.Input(id='ID_individual',
                                placeholder="Input the Individual ID",
                                style={'width': '20%'},
                                className='inputbox',
                                value=""
                                ),
                    html.Button('Search', id='search_individual', n_clicks=0, className="button"),
                    html.Div(id='output_individual', className='text2'),
                html.Br()])]),
            dcc.Tab(label='Business', children=[
                html.Br(),
                html.Div([html.Label('Tax ID',className="label"),
                    dcc.Input(id='ID_business',
                                placeholder="Input Business Tax ID",
                                style={'width': '20%'},
                                className='inputbox',
                                value=""
                                ),
                    html.Button('Search', id='search_business', n_clicks=0, className="button"),
                    html.Div(id='output_business', className='text2'),
                html.Br()])])])
    ])
    return sales_order_form_layout

@app.callback(dash.dependencies.Output('output_individual', 'children'),
[dash.dependencies.Input('search_individual', 'n_clicks')],
State('ID_individual', 'value'),
State('url', 'pathname'),
)

def search_individual(n_clicks, ID_individual, pathname):
    if n_clicks > 0:
        vin = pathname.split('/')[-2]
        sql = "SELECT * FROM IndividualPerson WHERE ID = %s"
        val = (ID_individual,)
        output = CONN.query(sql, val)
        if not output:
            return html.Div(dcc.Link('This customer is not found! Please add this new customer.', href=pathname + '/add_individual_customer_' + ID_individual, refresh=True))
        df = pd.DataFrame(output, columns=["Driver License ID", "Fname", "Lname", "CustomerID"])
        return html.Div([
            "This customer is found!",
            html.Table(children=[
            dbc.Container([
            html.Br(),
            dash_table.DataTable(
                id='individual_customer_table',
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('results'),
                column_selectable="single",
                ),])]),
            html.Br(),
            html.Label(df["CustomerID"][0], className="inputbox", id = "individual_customer_id", key=str(df["CustomerID"][0]), hidden = True),
            html.Div([html.Label('Vehicle VIN: ',className="label"),
                html.Label(vin, className="inputbox")]),
            html.Div([html.Label('Sold Price: ', className="label"),
                dcc.Input(id='soldprice', type='number',  className='inputbox')]),
            html.Div([html.Label('Sold Date: ',className="label"),
                html.Label(datetime.today().strftime("%Y-%m-%d"), className="inputbox")]),
            html.Button(id='submit-button-sell-vehicle', n_clicks=0, children='Sell This Vehicle', className="button"),
            html.Div(id='output-sell-vehicle-i', className='text2'),
            html.Div(id='return-to-sales-main-i')])

@app.callback(dash.dependencies.Output('output-sell-vehicle-i', 'children'),
[dash.dependencies.Input('submit-button-sell-vehicle', 'n_clicks')],
State('soldprice', 'value'),
State('individual_customer_id', 'key'),
State('url', 'pathname'),
)

def sell_individual(n_clicks, soldprice, individual_customer_id, pathname):
    if n_clicks > 0:
        vin = pathname.split('/')[-2]
        uname = pathname.split('/')[2]
        invoiceprice=pd.read_sql("SELECT Invoice_price FROM Vehicle WHERE vin=%s", mydb, params=(vin,))
        invoiceprice_t=float(invoiceprice.to_numpy().flatten())
        if soldprice is None or str(soldprice) == "":
            return html.Div(children='Please enter a sold price!')
        elif uname != 'roland' and float(soldprice) <= 0.95*invoiceprice_t:
            return html.Div(children='This sale is rejected! Price too low!')
        else:
            sql="UPDATE Vehicle SET Sold_date=%s, Sold_price=%s, CustomerID=%s, Sold_by=%s WHERE vin=%s"
            val=(datetime.today().strftime("%Y-%m-%d"), soldprice, individual_customer_id, uname, vin,)
            CONN.query(sql, val)
            dfv_update=pd.read_sql("SELECT vin as VIN, Type, Sold_date, Sold_price, CustomerID FROM Vehicle WHERE vin=%s", mydb, params=(vin,))
            tableoutput = html.Div([html.Table(children=[
                    dbc.Container([
                    dbc.Label('Bravo! You\'ve sold this vehicle!'),
                    dash_table.DataTable(
                        id='vin_table_update',
                        columns=[{"name": i, "id": i} for i in dfv_update.columns],
                        data=dfv_update.to_dict('records'),
                        column_selectable="single",
                        )])]),
                    dcc.ConfirmDialog(id='confirm-sold-dialog-i', message='This is to confirm you\'ve sold this vehicle! Click any button to return to sales main page!', displayed=False)
                    ])
            return tableoutput

@app.callback(dash.dependencies.Output('confirm-sold-dialog-i', 'displayed'),
[dash.dependencies.Input('output-sell-vehicle-i', 'children')])

def confirm_sold_individual(content):
    if content != "":
        return True
    else:
        return False

@app.callback(dash.dependencies.Output('return-to-sales-main-i', 'children'),
[dash.dependencies.Input('confirm-sold-dialog-i', 'submit_n_clicks'),
dash.dependencies.Input('confirm-sold-dialog-i', 'cancel_n_clicks')],
State('url', 'pathname'))

def return_to_sales_main_i(snc, cnc, pathname):
    uname = pathname.split('/')[2]
    if snc or cnc:
        return dcc.Location(href='/logged_in_sales/' + uname, id='sales_main_page')

@app.callback(dash.dependencies.Output('output_business', 'children'),
[dash.dependencies.Input('search_business', 'n_clicks')],
State('ID_business', 'value'),
State('url', 'pathname'),
)

def search_business(n_clicks, ID_business, pathname):
    if n_clicks > 0:
        vin = pathname.split('/')[-2]
        sql = "SELECT * FROM Business WHERE Tax_ID = %s"
        val = (ID_business,)
        output = CONN.query(sql, val)
        if not output:
            return html.Div(dcc.Link('This customer is not found! Please add this new customer.', href=pathname + '/add_business_customer_' + ID_business, refresh=True))
        df = pd.DataFrame(output, columns=["Tax ID", "Title", "Business_name", "Fname", "Lname", "CustomerID"])
        return html.Div([
            "This customer is found!",
            html.Table(children=[
            dbc.Container([
            html.Br(),
            dash_table.DataTable(
                id='business_customer_table',
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('results'),
                column_selectable="single",
                ),])]),
            html.Br(),
            html.Label(df["CustomerID"][0], className="inputbox", id = "business_customer_id", key=str(df["CustomerID"][0]), hidden = True),
            html.Div([html.Label('Vehicle VIN: ',className="label"),
                html.Label(vin, className="inputbox")]),
            html.Div([html.Label('Sold Price: ', className="label"),
                dcc.Input(id='soldprice_business', type='number',  className='inputbox')]),
            html.Div([html.Label('Sold Date: ',className="label"),
                html.Label(datetime.today().strftime("%Y-%m-%d"), className="inputbox")]),
            html.Button(id='submit-button-sell-vehicle-business', n_clicks=0, children='Sell This Vehicle', className="button"),
            html.Div(id='output-sell-vehicle-b', className='text2'),
            html.Div(id='return-to-sales-main-b')])

@app.callback(dash.dependencies.Output('output-sell-vehicle-b', 'children'),
[dash.dependencies.Input('submit-button-sell-vehicle-business', 'n_clicks')],
State('soldprice_business', 'value'),
State('business_customer_id', 'key'),
State('url', 'pathname'),
)

def sell_business(n_clicks, soldprice_business, business_customer_id, pathname):
    if n_clicks > 0:
        vin = pathname.split('/')[-2]
        uname = pathname.split('/')[2]
        invoiceprice=pd.read_sql("SELECT Invoice_price FROM Vehicle WHERE vin=%s", mydb, params=(vin,))
        invoiceprice_t=float(invoiceprice.to_numpy().flatten())
        
        if soldprice_business is None or str(soldprice_business) == "":
            return html.Div(children='Please enter a sold price!')
        elif uname != 'roland' and float(soldprice_business) <= 0.95*invoiceprice_t:
            return html.Div(children='This sale is rejected! Price too low!')
        else:
            sql="UPDATE Vehicle SET Sold_date=%s, Sold_price=%s, CustomerID=%s, Sold_by=%s WHERE vin=%s"
            val=(datetime.today().strftime("%Y-%m-%d"), soldprice_business, business_customer_id, uname, vin,)
            CONN.query(sql, val)
            dfv_update=pd.read_sql("SELECT vin as VIN, Type, Sold_date, Sold_price, CustomerID FROM Vehicle WHERE vin=%s", mydb, params=(vin,))
            return html.Div([html.Table(children=[
                    dbc.Container([
                    dbc.Label('Bravo! You\'ve sold this vehicle!'),
                    dash_table.DataTable(
                        id='vin_table_update',
                        columns=[{"name": i, "id": i} for i in dfv_update.columns],
                        data=dfv_update.to_dict('records'),
                        column_selectable="single",
                        )])]),
                    dcc.ConfirmDialog(id='confirm-sold-dialog-b', message='This is to confirm you\'ve sold this vehicle! Click any button to return to sales main page!', displayed=False),
                    ])

@app.callback(dash.dependencies.Output('confirm-sold-dialog-b', 'displayed'),
[dash.dependencies.Input('output-sell-vehicle-b', 'children')])

def confirm_sold_business(content):
    if content != "":
        return True
    else:
        return False

@app.callback(dash.dependencies.Output('return-to-sales-main-b', 'children'),
[dash.dependencies.Input('confirm-sold-dialog-b', 'submit_n_clicks'),
dash.dependencies.Input('confirm-sold-dialog-b', 'cancel_n_clicks')],
State('url', 'pathname'))

def return_to_sales_main_b(snc, cnc, pathname):
    uname = pathname.split('/')[2]
    if snc or cnc:
        return dcc.Location(href='/logged_in_sales/' + uname, id='sales_main_page_b')


def main_page():
    index_page = html.Div([
    html.H1("Welcome to the Jaunty Jalopies Portal!"),
    html.Br(),
    html.H3("Privileged User? Please Login!"),
    html.Div([
        "Username: ",
        dcc.Input(id='username', type='text', value='')]),
    html.Br(),
    html.Div([
        "Password: ",
        dcc.Input(id='password', type='password', value='')]),
    html.Br(),
    html.Button(id='submit-button-login', n_clicks=0, children='Submit'),
    html.Br(),
    html.Div(id='output-login-outcome'),
    html.Br(),
    html.Br(),
    html.Div([
    html.H3("Search Vehicle"),
    html.Div("Total number of avaliable vehicles: {}".format(get_total_number_of_avaliable_vehicles())),
    html.Br(),
    html.Br(),
    html.Label('Vehicle Type'),
    html.Div([dcc.Dropdown(
        id='vehicle_type',
        options= get_vehicle_type(),
        style={'width': '50%'},
        placeholder = 'Select a vehicle type'),]),
    html.Br(),
    html.Br(),
    html.Label('Vehicle Manufacturer'),
    html.Div([dcc.Dropdown(
        id='vehicle_manufacturer',
        options=[
            {'label':i, 'value':i} for i in get_vehicle_manufacturer()['vm'].unique()
        ],
        style={'width': '50%'},
        placeholder = 'Select a manufacturer'),]),
    html.Br(),
    html.Br(),
    html.Label('Year'),
    html.Div([dcc.Dropdown(
        id='vehicle_year',
        options=[{'label':x, 'value': x} for x in range( get_model_year(), 1959, -1)],
             placeholder = 'Select a year from current to 1960',
             style={'width': '50%'},),]),
    html.Br(),
    html.Br(),
    html.Label('Color'),
    html.Div([dcc.Dropdown(
        id='vehicle_color',
        options=[{'label':i, 'value':i} for i in get_vehicle_color()['vc'].unique()],
        placeholder = 'Select a color',
        style={'width': '50%'}),]),
    html.Br(),
    html.Br(),
    html.Label('List Price'),
    html.Div([
        daq.NumericInput(id='list_price_low_value', size=100, max=sys.maxsize, label="lowest value"),
        daq.NumericInput(id='list_price_high_value', size=100, max=sys.maxsize, label="highest value")]),
    html.Br(),
    html.Br(),
    html.Label('Keywords'),
    html.Div([dcc.Textarea(id='description', placeholder="", style={'width':'80%', 'height': 100}),]),
    html.Br(),
    html.Br(),
    html.Button(id='query-search-vehicle-button-ana', n_clicks=0, children='Submit'),
    html.Br(),
    html.Br(),
    html.Div(id='out-vehicle-anonymous-table')])
    ])
    return index_page

@app.callback(dash.dependencies.Output('output-login-outcome', 'children'),
[dash.dependencies.Input('submit-button-login', 'n_clicks')],
State('username', 'value'),
State('password', 'value'),
)

def log_in(n_clicks, uname, passw):
    query = "SELECT Username, Password FROM User GROUP BY Username"
    df = pd.read_sql(query,mydb)
    li=df.to_dict('records')
    newli={row["Username"]: row["Password"] for row in li}
    if uname =='' or uname == None or passw =='' or passw == None:
        return html.Div(children='')
    if uname not in newli:
        return html.Div(children='Incorrect Username or Password!')
    if newli[uname]==passw:
        rolequery="SELECT Role FROM UserRole INNER JOIN User ON UserRole.Username = User.Username WHERE User.Username = \'%s\'" % (uname)
        # role = pd.read_sql(rolequery,mydb)['Role'][0]

        user_roles = pd.read_sql(rolequery,mydb)['Role'].to_dict().values()
        if "owner" in user_roles:
            return html.Div(dcc.Link('Access Granted!', href='/logged_in_admin/' + uname, refresh=True))
        else:
            role = list(user_roles)[0]
        if role=="sales_person":
            return html.Div(dcc.Link('Access Granted!', href='/logged_in_sales/' + uname, refresh=True))
        elif role=="service_writer":
            return html.Div(dcc.Link('Access Granted!', href='/logged_in_service_writer/'+uname, refresh=True))
        elif role=="inventory_clerk":
            return html.Div(dcc.Link('Access Granted!', href='/logged_in_inventory_clerk/%s/%s' % (uname, passw), refresh=True))
        elif role=="manager":
            return html.Div(dcc.Link('Access Granted!', href='/logged_in_manager/' + uname, refresh=True))
        # elif role=="admin":
        #     return html.Div(dcc.Link('Access Granted!', href='/logged_in_admin', refresh=True))
    else:
        return html.Div(children='Incorrect Username or Password!')

@app.callback(
dash.dependencies.Output('out-vehicle-anonymous-table', 'children'),
[dash.dependencies.Input('query-search-vehicle-button-ana', 'n_clicks')],
State('vehicle_type', 'value'),
State('vehicle_manufacturer', 'value'),
State('vehicle_year', 'value'),
State('vehicle_color', 'value'),
State('list_price_low_value', 'value'),
State('list_price_high_value', 'value'),
State('description', 'value'),
)

def query_vehicle_anonymous(n_clicks, vehicle_type, vehicle_manufacturer, vehicle_year, 
                  vehicle_color, list_price_low_value, list_price_high_value,
                  description):
    if n_clicks == 0:
        return
    if description != None:
        description = description.strip()
    value_list = [vehicle_type, vehicle_manufacturer, vehicle_year, vehicle_color,
    list_price_low_value, list_price_high_value, description]
    if list(set(value_list)) == [None]:
        return "Need input the search condition!"
    name_list = [
                "vehicle_type",
                "vehicle_manufacturer", 
                "vehicle_year",
                "vehicle_color",
                "list_price_low_value",
                "list_price_high_value",
                "description"
                ]
    res = {}
    for i, x in enumerate(value_list):
        if type(x) is tuple:
            x = x[0]
        res[name_list[i]] = str(x)
    value = ()
    if res["description"] == 'None':
        sql = "SELECT v.VIN, v.Type, v.Model_year, v.Manufacturer_name, v.Model_name, \
        GROUP_CONCAT(vc.color) AS Color, \
            v.Invoice_price*1.25 \
                FROM Vehicle AS v INNER JOIN VehicleColor AS vc ON vc.VIN = v.VIN WHERE v.Sold_date IS NULL "
    else:
        sql = "SELECT v.VIN, v.Type, v.Model_year, v.Manufacturer_name, v.Model_name, \
        GROUP_CONCAT(vc.color) AS Color, \
            IF(Description LIKE BINARY %s, 'Yes', 'No') AS 'Match Description or not',\
            v.Invoice_price*1.25 \
                FROM Vehicle AS v INNER JOIN VehicleColor AS vc ON vc.VIN = v.VIN WHERE v.Sold_date IS NULL "
        value += ("%" + res["description"]+ "%",)
    if res["vehicle_type"] != 'None':
        sql += "AND v.Type = %s "
        value += (res["vehicle_type"],)
    if res["vehicle_manufacturer"] != 'None':
        sql += "AND v.Manufacturer_name = %s "
        value += (res["vehicle_manufacturer"],)
    if res["vehicle_year"] != 'None':
        sql += "AND v.Model_year = %s "
        value += (res["vehicle_year"],)
    if res["vehicle_color"] != 'None':
        sql += "AND vc.Color in (%s) "
        value += (res["vehicle_color"],)
    if res["list_price_low_value"] != 'None' and res["list_price_high_value"] != 'None':
        sql += "AND v.Invoice_price BETWEEN %s/1.25 AND %s/1.25 "
        value += (res["list_price_low_value"], res["list_price_high_value"],)
    if res["list_price_low_value"] == 'None' and res["list_price_high_value"] != 'None':
        sql += "AND v.Invoice_price <= %s/1.25 "
        value += (res["list_price_high_value"],)
    if res["list_price_low_value"] != 'None' and res["list_price_high_value"] == 'None':
        sql += "AND v.Invoice_price >= %s/1.25 "
        value += (res["list_price_low_value"],)
    if res["description"] != 'None':
            sql += "AND ( v.Manufacturer_name LIKE BINARY %s OR v.Model_year LIKE BINARY %s OR v.Model_name LIKE BINARY %s OR v.Description LIKE BINARY %s) "
            value += ("%" + res["description"]+ "%","%" + res["description"]+ "%", "%" + res["description"]+ "%", "%" + res["description"]+ "%",)

    sql += "GROUP BY v.VIN ORDER BY v.VIN ASC"
    output = CONN.query(sql, value)
    if len(output) == 0:
        return "Sorry, it looks like we don't have that in stock!"
   
    if res["description"] == 'None':
        df = pd.DataFrame(output, columns=["VIN", "Type", "Model_year", 
                                   "Manufacturer_name", "Model_name", "Color",
                                   "Price"])
        df['Price'] = df['Price'].apply(lambda x: round(x, 2))
        df["VIN"] = "[" + df["VIN"] + "](/anonymous_view_vehicle_detail/" + df["VIN"] + ")"
        # return generate_vehicle_table(df)
        return html.Table(children=[
			dbc.Container([
				dbc.Label('Results'),
				html.Br(),
				dash_table.DataTable(
					#columns=[{"name": i, "id": i} for i in df.columns],
                    columns=[{"name": "VIN", "id": "VIN", "type": "text", "presentation": "markdown"}, {"name": "Type", "id": "Type"}, {"name": "Model_year", "id": "Model_year"}, {"name": "Manufacturer_name", "id": "Manufacturer_name"}, {"name": "Model_name", "id": "Model_name"}, {"name": "Color", "id": "Color"}, {"name": "Price", "id": "Price"}],
                    data=df.to_dict('results'),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="single",
                       )])])
    else:
        df = pd.DataFrame(output, columns=["VIN", "Type", "Model_year", 
                                   "Manufacturer_name", "Model_name", "Color",
                                   "Match Description", "Price"])
        df['Price'] = df['Price'].apply(lambda x: round(x, 2))
        df["VIN"] = "[" + df["VIN"] + "](/anonymous_view_vehicle_detail/" + df["VIN"] + ")"
        return html.Table(children=[
            dbc.Container([
                dbc.Label('Results'),
                html.Br(),
                dash_table.DataTable(
                    #columns=[{"name": i, "id": i} for i in df.columns],
                    columns=[{"name": "VIN", "id": "VIN", "type": "text", "presentation": "markdown"}, {"name": "Type", "id": "Type"}, {"name": "Model_year", "id": "Model_year"}, {"name": "Manufacturer_name", "id": "Manufacturer_name"}, {"name": "Model_name", "id": "Model_name"}, {"name": "Color", "id": "Color"}, {"name": "Match Description", "id": "Match Description"}, {"name": "Price", "id": "Price"}],
                    data=df.to_dict('results'),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="single",
                       )])])
    
def layout_logged_in_sales(username):
    logged_in_sales = html.Div([
    html.Div([dcc.Link(html.Button('Log Out'), href='/'),
              dcc.Link(html.Button('Return to Owner Main Menu'), href='/logged_in_admin/' + username, refresh=True) if username == "roland" else '',
    html.H1(children="Welcome to the Jaunty Jalopies Sales Portal!")]),
    html.Br(),
    html.H3("Search Vehicle"),
    html.Div("Total number of avaliable vehicles: {}".format(get_total_number_of_avaliable_vehicles())),

    html.Br(),
    html.Br(),
    html.Label('VIN'),
    html.Div([dcc.Dropdown(
        id='vin',
        options=[
            {'label':i, 'value':i} for i in get_vin()['vin'].unique()
        ],
        style={'width': '50%'},
        placeholder = 'Select a vehicle VIN'),]),
    html.Br(),
    html.Br(),
    html.Label('Vehicle Type'),
    html.Div([dcc.Dropdown(
        id='vehicle_type',
        options= get_vehicle_type(),
        style={'width': '50%'},
        placeholder = 'Select a vehicle type'),]),
    html.Br(),
    html.Br(),
    html.Label('Vehicle Manufacturer'),
    html.Div([dcc.Dropdown(
        id='vehicle_manufacturer',
        options=[
            {'label':i, 'value':i} for i in get_vehicle_manufacturer()['vm'].unique()
        ],
        style={'width': '50%'},
        placeholder = 'Select a manufacturer'),]),
    html.Br(),
    html.Br(),
    html.Label('Year'),
    html.Div([dcc.Dropdown(
        id='vehicle_year',
        options=[{'label':x, 'value': x} for x in range(get_model_year(), 1959, -1)],
             placeholder = 'Select a year from current to 1960',
             style={'width': '50%'},
             ),]),
    html.Br(),
    html.Br(),
    html.Label('Color'),
    html.Div([dcc.Dropdown(
        id='vehicle_color',
        options=[{'label':i, 'value':i} for i in get_vehicle_color()['vc'].unique()],
        placeholder = 'Select a color'),]),
    html.Br(),
    html.Br(),
    html.Label('List Price'),
    html.Div([
        daq.NumericInput(id='list_price_low_value',size=100, max=sys.maxsize, label="lowest value"),
        daq.NumericInput(id='list_price_high_value', size=100, max=sys.maxsize, label="highest value")]),
    html.Br(),
    html.Br(),
    html.Label('Keywords'),
    html.Div([dcc.Textarea(id='description', placeholder="", style={'width':'80%', 'height': 100}),]),
    html.Br(),
    html.Br(),
    html.Button(id='query-search-vehicle-button', n_clicks=0, children='Submit'),
    html.Br(),
    html.Br(),
    html.Div(id='output-search-vehicle-table')
])
    return logged_in_sales

@app.callback(
dash.dependencies.Output('output-search-vehicle-table', 'children'),
[dash.dependencies.Input('query-search-vehicle-button', 'n_clicks')],
State('vin', 'value'),
State('vehicle_type', 'value'),
State('vehicle_manufacturer', 'value'),
State('vehicle_year', 'value'),
State('vehicle_color', 'value'),
State('list_price_low_value', 'value'),
State('list_price_high_value', 'value'),
State('description', 'value'),
State('url', 'pathname'),
)
def query_vehicle(n_clicks, vin, vehicle_type, vehicle_manufacturer, vehicle_year, 
                  vehicle_color, list_price_low_value, list_price_high_value,
                  description, pathname):
    uname = pathname.split('/')[2]
    if description != None:
        description = description.strip()
    if n_clicks == 0:
        return
    value_list = [vin, vehicle_type, vehicle_manufacturer, vehicle_year, 
    vehicle_color, list_price_low_value, list_price_high_value, description]
    if list(set(value_list)) == [None]:
        return "Need input the search condition!"
    name_list = [
                "vin",
                "vehicle_type",
                "vehicle_manufacturer", 
                "vehicle_year",
                "vehicle_color",
                "list_price_low_value",
                "list_price_high_value",
                "description"
                ]
    res = {}
    for i, x in enumerate(value_list):
        if type(x) is tuple:
            x = x[0]
        res[name_list[i]] = str(x)
    value = ()
    if res["description"] == 'None':
        sql = "SELECT v.VIN, v.Type, v.Model_year, v.Manufacturer_name, v.Model_name, \
        GROUP_CONCAT(vc.color) AS Color, \
            v.Invoice_price*1.25 \
                FROM Vehicle AS v INNER JOIN VehicleColor AS vc ON vc.VIN = v.VIN WHERE v.Sold_date IS NULL "
    else:
        sql = "SELECT v.VIN, v.Type, v.Model_year, v.Manufacturer_name, v.Model_name, \
        GROUP_CONCAT(vc.color) AS Color, \
            IF(Description LIKE BINARY %s, 'Yes', 'No') AS 'Match Description or not',\
            v.Invoice_price*1.25 \
                FROM Vehicle AS v INNER JOIN VehicleColor AS vc ON vc.VIN = v.VIN WHERE v.Sold_date IS NULL "
        value += ("%" + res["description"]+ "%",)

    if res["vin"] != 'None':
        sql += "AND v.Vin = %s "
        value += (res["vin"],)
    if res["vehicle_type"] != 'None':
        sql += "AND v.Type = %s "
        value += (res["vehicle_type"],)
    if res["vehicle_manufacturer"] != 'None':
        sql += "AND v.Manufacturer_name = %s "
        value += (res["vehicle_manufacturer"],)
    if res["vehicle_year"] != 'None':
        sql += "AND v.Model_year = %s "
        value += (res["vehicle_year"],)
    if res["vehicle_color"] != 'None':
        sql += "AND vc.Color in (%s) "
        value += (res["vehicle_color"],)
    if res["list_price_low_value"] != 'None' and res["list_price_high_value"] != 'None':
        sql += "AND v.Invoice_price BETWEEN %s/1.25 AND %s/1.25 "
        value += (res["list_price_low_value"], res["list_price_high_value"],)
    if res["list_price_low_value"] == 'None' and res["list_price_high_value"] != 'None':
        sql += "AND v.Invoice_price <= %s/1.25 "
        value += (res["list_price_high_value"],)
    if res["list_price_low_value"] != 'None' and res["list_price_high_value"] == 'None':
        sql += "AND v.Invoice_price >= %s/1.25 "
        value += (res["list_price_low_value"],)
    if res["description"] != 'None':
            sql += "AND ( v.Manufacturer_name LIKE BINARY %s OR v.Model_year LIKE BINARY %s OR v.Model_name LIKE BINARY %s OR v.Description LIKE BINARY %s) "
            value += ("%" + res["description"]+ "%","%" + res["description"]+ "%", "%" + res["description"]+ "%", "%" + res["description"]+ "%",)

    sql += "GROUP BY v.VIN ORDER BY v.VIN ASC"
    
    output = CONN.query(sql, value)

    if len(output) == 0:
        return "Sorry, it looks like we don’t have that in stock!"
   
    if res["description"] == 'None':
        df = pd.DataFrame(output, columns=["VIN", "Type", "Model_year", 
                                   "Manufacturer_name", "Model_name", "Color",
                                   "Price"])
        df['Price'] = df['Price'].apply(lambda x: round(x, 2))
        df["VIN"] = "[" + df["VIN"] + "](/logged_in_sales/" + uname +"/view_vehicle_detail/" + df["VIN"] + ")"
        return html.Table(children=[
            dbc.Container([
                dbc.Label('Results'),
                html.Br(),
                dash_table.DataTable(
                    columns=[{"name": "VIN", "id": "VIN", "type": "text", "presentation": "markdown"}, {"name": "Type", "id": "Type"}, {"name": "Model_year", "id": "Model_year"}, {"name": "Manufacturer_name", "id": "Manufacturer_name"}, {"name": "Model_name", "id": "Model_name"}, {"name": "Color", "id": "Color"}, {"name": "Price", "id": "Price"}],
                    data=df.to_dict('results'),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="single",
                       )])])
    else:
        df = pd.DataFrame(output, columns=["VIN", "Type", "Model_year", 
                                   "Manufacturer_name", "Model_name", "Color",
                                   "Match Description", "Price"])
        df['Price'] = df['Price'].apply(lambda x: round(x, 2))
        df["VIN"] = "[" + df["VIN"] + "](/logged_in_sales/" + uname +"/view_vehicle_detail/" + df["VIN"] + ")"
        return html.Table(children=[
            dbc.Container([
                dbc.Label('Results'),
                html.Br(),
                dash_table.DataTable(
                    columns=[{"name": "VIN", "id": "VIN", "type": "text", "presentation": "markdown"}, {"name": "Type", "id": "Type"}, {"name": "Model_year", "id": "Model_year"}, {"name": "Manufacturer_name", "id": "Manufacturer_name"}, {"name": "Model_name", "id": "Model_name"}, {"name": "Color", "id": "Color"}, {"name": "Match Description", "id": "Match Description"}, {"name": "Price", "id": "Price"}],
                    data=df.to_dict('results'),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="single",
                       )])])

# add customer for service writer
def service_add_customer_ip_layout(username, vin, ip_id):
    service_add_customer_ip_layout = html.Div([
        html.Div([dcc.Link(html.Button('Log Out'), href='/'),
                 dcc.Link(html.Button('Return to Service Witer Portal'), href='/logged_in_service_writer'),
           ]),
        html.H3("Please enter the detail information to add this customer!"),
        html.Div(children=[
                html.Br(),
                html.Label('Driver License Number: '),
                html.Label(ip_id),
                html.Br(),
                html.Label('First Name: '),
                dcc.Input(id='Fname_i', value='', type='text'),
                html.Br(),
                html.Label('Last Name: '),
                dcc.Input(id='Lname_i', value='', type='text'),
                html.Br(),
                html.Label('Email: '),
                dcc.Input(id='email_i', value='', type='email'),        
                html.Br(),
                html.Label('Street: '),
                dcc.Input(id='street_i', value='', type='text'),
                html.Br(),
                html.Label('City: '),
                dcc.Input(id='city_i', value='', type='text'),
                html.Br(),
                html.Label('State: '),
                dcc.Input(id='state_i', value='', type='text'),
                html.Br(),
                html.Label('Zipcode: '),
                dcc.Input(id='zipcode_i', value='', type='number'),
                html.Br(),
                html.Label('Phone: '),
                dcc.Input(id='phone_i', value='', type='number'),
                ], style={'padding': 50, 'font-size':'16px'}),
                dcc.Link(html.Button("Cancel"), id='btn-return_i', href='/add_repair/{}/{}'.format(username, vin), refresh=True),
                html.Button('Save', id='btn-save_i', n_clicks=0),
                html.Div(id='s_add-success_i'),
                html.Div(id='return-to-repair-add-customer-ip'),
    ])
    return service_add_customer_ip_layout

@app.callback(
    Output('s_add-success_i', 'children'),
    Input("btn-save_i", "n_clicks"),
    # State('driverlicense','value'),
    State("Fname_i", "value"), 
    State("Lname_i", "value"), 
    State("email_i", "value"), 
    State("street_i", "value"), 
    State("city_i", "value"), 
    State("state_i", "value"), 
    State("zipcode_i", "value"), 
    State("phone_i", "value"),
    State("url", "pathname") 
)
def add_individual_repair_customer(n_clicks, Fname_i, Lname_i, email_i, street_i, city_i, state_i, zipcode_i, phone_i, pathname):
    driver_i=pathname.split('/')[-1]
    if n_clicks > 0:
        dict_temp = {"Driver License Number":driver_i, "Fisrt Name":Fname_i,
        "Last Name": Lname_i, "Street":street_i, "City":city_i, "State":state_i, 
            "Zipcode":zipcode_i, "Phone:": phone_i}
        for key, val in dict_temp.items():
            if val == "":
                return " {} Field can not be Empty".format(key)
        query1="INSERT INTO Customer (Email, Street, City, State, Zipcode, Phone_number) VALUES('%s','%s','%s','%s','%s','%s')"%(email_i, street_i, city_i, state_i, zipcode_i, phone_i)
        query2="INSERT INTO IndividualPerson (ID, Fname, Lname, CustomerID) VALUES ('%s', '%s', '%s', LAST_INSERT_ID())"%(driver_i, Fname_i, Lname_i)
        cursor.execute(query1)
        mydb.commit()
        cursor.execute(query2)
        mydb.commit()
        return html.Div([html.Label('Sucessfully add this customer', id='repair_id_customer_label_ip'),
            dcc.ConfirmDialog(id='confirm-repair-add-customer-ip-dialog', message='This is to confirm you\'ve added the customer! Click any button to return to add vehicle page!', displayed=False)])

@app.callback(dash.dependencies.Output('confirm-repair-add-customer-ip-dialog', 'displayed'),
[dash.dependencies.Input('repair_id_customer_label_ip', 'children')])
def confirm_repair_customer_p(content):
    if content != "":
        return True
    else:
        return False

@app.callback(dash.dependencies.Output('return-to-repair-add-customer-ip', 'children'),
[dash.dependencies.Input('confirm-repair-add-customer-ip-dialog', 'submit_n_clicks'),
dash.dependencies.Input('confirm-repair-add-customer-ip-dialog', 'cancel_n_clicks')],
State('url', 'pathname'))
def return_to_repair_main(snc, cnc, pathname):
    uname = pathname.split('/')[-3]
    vin = pathname.split('/')[-2]
    if snc or cnc:
        return dcc.Location(href='/add_repair/{}/{}'.format(uname, vin), id='add_repair_page')

def service_add_customer_b_layout(username, vin,tax_id):       
    service_add_customer_b_layout = html.Div([
        html.Div([dcc.Link(html.Button('Log Out'), href='/'),
                dcc.Link(html.Button('Return to Service Witer Portal'), href='/logged_in_service_writer'),
           ]),
        html.H3("Please enter the detail information to add this customer!"),
        html.Div(children=[
                    html.Br(),
                    html.Label('Tax ID: '),
                    html.Label(tax_id),
                    html.Br(),
                    html.Label('Title: '),
                    dcc.Input(id='title', value='', type='text'),
                    html.Br(),
                    html.Label('Business Name: '),
                    dcc.Input(id='businessname', value='', type='text'),
                    html.Br(),
                    html.Label('First Name: '),
                    dcc.Input(id='Fname_b', value='', type='text'),
                    html.Br(),
                    html.Label('Last Name: '),
                    dcc.Input(id='Lname_b', value='', type='text'),
                    html.Br(),
                    html.Label('Email: '),
                    dcc.Input(id='email_b', value='', type='email'),        
                    html.Br(),
                    html.Label('Street: '),
                    dcc.Input(id='street_b', value='', type='text'),
                    html.Br(),
                    html.Label('City: '),
                    dcc.Input(id='city_b', value='', type='text'),
                    html.Br(),
                    html.Label('State: '),
                    dcc.Input(id='state_b', value='', type='text'),
                    html.Br(),
                    html.Label('Zipcode: '),
                    dcc.Input(id='zipcode_b', value='', type='number'),
                    html.Br(),
                    html.Label('Phone: '),
                    dcc.Input(id='phone_b', value='', type='number'),
                ], style={'padding': 50, 'font-size':'16px'}),
                dcc.Link(html.Button("Cancel"), id='btn-return_b', href='/add_repair/{}/{}'.format(username, vin), refresh=True),
                html.Button('Save', id='btn-save_b', n_clicks=0),
                html.Div(id='s_add-success_b'),
                html.Div(id='return-to-repair-add-customer-b'),
    ])
    return service_add_customer_b_layout

@app.callback(
    Output('s_add-success_b', 'children'),
    Input("btn-save_b", "n_clicks"),
    # State('Tax_ID_b','value'),
    State("title", "value"), 
    State("businessname", "value"), 
    State("Fname_b", "value"), 
    State("Lname_b", "value"), 
    State("email_b", "value"), 
    State("street_b", "value"), 
    State("city_b", "value"), 
    State("state_b", "value"), 
    State("zipcode_b", "value"), 
    State("phone_b", "value"),
    State("url", "pathname") 
 
)
def add_business_customer(n_clicks, title, businessname, Fname_b, Lname_b, email_b, street_b, city_b, state_b, zipcode_b, phone_b, pathname):
    tid=pathname.split('/')[-1]
    if n_clicks > 0:
        dict_temp = {"Business Name":businessname, "Fisrt Name":Fname_b,
        "Last Name": Lname_b, "Street":street_b, "City":city_b, "State":state_b, 
            "Zipcode":zipcode_b, "Phone:": phone_b}
        for key, val in dict_temp.items():
            if val=="":
                return " {} Field can not be Empty".format(key)
        query1="INSERT INTO Customer (Email, Street, City, State, Zipcode, Phone_number) VALUES('%s','%s','%s','%s','%s','%s')"%(email_b, street_b, city_b, state_b, zipcode_b, phone_b)
        query2="INSERT INTO Business (Tax_ID, Title, Business_name, Fname, Lname, CustomerID) VALUES ('%s', '%s', '%s', '%s', '%s', LAST_INSERT_ID())"%(tid, title, businessname, Fname_b, Lname_b)
        cursor.execute(query1)
        mydb.commit()
        cursor.execute(query2)
        mydb.commit()
        return html.Div([html.Label('Customer added successfully!', id='repair_id_customer_label_b'),
                dcc.ConfirmDialog(id='confirm-repair-add-customer-b-dialog', message='This is to confirm you\'ve added the customer! Click any button to return to add vehicle page!', displayed=False),
        ])

@app.callback(dash.dependencies.Output('confirm-repair-add-customer-b-dialog', 'displayed'),
[dash.dependencies.Input('repair_id_customer_label_b', 'children')])
def confirm_repair_customer_p(content):
    if content != "":
        return True
    else:
        return False

@app.callback(dash.dependencies.Output('return-to-repair-add-customer-b', 'children'),
[dash.dependencies.Input('confirm-repair-add-customer-b-dialog', 'submit_n_clicks'),
dash.dependencies.Input('confirm-repair-add-customer-b-dialog', 'cancel_n_clicks')],
State('url', 'pathname'))
def return_to_repair_main(snc, cnc, pathname):
    uname = pathname.split('/')[-3]
    vin = pathname.split('/')[-2]
    if snc or cnc:
        return dcc.Location(href='/add_repair/{}/{}'.format(uname, vin), id='add_repair_page')

def logged_in_service_writer(username):
    logged_in_service_writer = html.Div([
    html.Div([dcc.Link(html.Button('Log Out'), href='/'),
              dcc.Link(html.Button('Return to Owner Main Menu'), href='/logged_in_admin/' + username,
                       refresh=True) if username == "roland" else '',
    html.H1(children="Welcome to the Jaunty Jalopies Service Writer Portal!")]),
    html.Br(),
    html.Div([
        "To Open A Repair Form: ",
        dcc.Link(html.Button('Open Repair Form'), href='/repair_form_main_page/' + username)
    ])
])
    return logged_in_service_writer

def repair_form_main_page(username):
    repair_form_main_page = html.Div([
    html.Div([dcc.Link(html.Button('Log Out'), href='/'),
              dcc.Link(html.Button('Return to Service Witer Portal'), href='/logged_in_service_writer/{}'.format(username)),
           ]),
	html.H1("REPAIR FORM"),
	html.Br(), html.Hr(), html.Br(),
	html.Label('Search Vehicle'),
	dcc.Input(id='vin', placeholder='Input a vehicle VIN'),html.Br(),html.Br(),
	html.Button(id='query-button', n_clicks=0, children='Check'),
    html.Div(id='output-repair-search-vehicle'),
	html.Br(),html.Br(),
	])
    return repair_form_main_page

@app.callback(
Output('output-repair-search-vehicle', 'children'),
[Input('query-button', 'n_clicks')],
State('vin', 'value'),
State('url', 'pathname'),)
def check_vehicle(n_clicks,vin, pathname):
    if n_clicks == 0:
        return
    username = pathname.split('/')[-1]
    # check vehcile is exist or not
    dfv_0 = pd.read_sql("SELECT v.vin, v.CustomerID, v.Type, v.Model_name, v.Manufacturer_name, GROUP_CONCAT(vc.color) AS Color, v.Model_year, \
        v.Sold_date FROM Vehicle as v INNER JOIN VehicleColor AS vc ON v.VIN=vc.VIN WHERE v.VIN = %s", mydb, params=(vin,))
    # check vehicle has repair record
    dfv = pd.read_sql("select rv.vin, r.CustomerID, rv.Type, rv.Model_name, rv.Manufacturer_name, rv.Color, rv.Model_year, rv.Sold_date, r.Start_date, r.Complete_date \
        FROM (SELECT v.vin, v.CustomerID, v.Type, v.Model_name, v.Manufacturer_name, GROUP_CONCAT(vc.color) AS Color, v.Model_year, v.Sold_date \
            FROM Vehicle as v INNER JOIN VehicleColor AS vc ON v.VIN=vc.VIN WHERE v.VIN = %s AND v.Sold_date is NOT NULL GROUP BY v.VIN) as rv \
                    Inner Join Repair as r on r.vin = rv.VIN;", mydb, params=(vin,))
    # check vehicle is reparing but not finished
    dfv1 = pd.read_sql("select rv.vin, r.CustomerID, rv.Type, rv.Model_name, rv.Manufacturer_name, rv.Color, rv.Model_year, rv.Sold_date, r.Start_date, r.Complete_date \
        FROM (SELECT v.vin, v.CustomerID, v.Type, v.Model_name, v.Manufacturer_name, GROUP_CONCAT(vc.color) AS Color, v.Model_year, v.Sold_date \
            FROM Vehicle as v INNER JOIN VehicleColor AS vc ON v.VIN=vc.VIN WHERE v.VIN = %s AND v.Sold_date is NOT NULL GROUP BY v.VIN) as rv \
                    Inner Join Repair as r on r.vin = rv.VIN \
                        where r.Start_date is NOT NULL and r.Complete_date is NULL", mydb, params=(vin,))
    dfv2 = pd.read_sql("SELECT v.vin, v.CustomerID, v.Type, v.Model_name, v.Manufacturer_name, GROUP_CONCAT(vc.color) AS Color, v.Model_year, \
        v.Sold_date FROM Vehicle as v INNER JOIN VehicleColor AS vc ON v.VIN=vc.VIN WHERE v.VIN = %s and v.Sold_date is NULL", mydb, params=(vin,))

    if dfv_0.iloc()[0][0] == None:
        return "Not found Vehicle!"
    if dfv2.iloc()[0][0] != None:
        return "The vehicle have not been sold yet!"
    elif len(dfv) == 0 and len(dfv_0) != 0:
        return html.Table(children=[
            dbc.Container([
                dbc.Label('Vehcile has no repair history, please Add Repair'),
                html.Br(),
                dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in dfv_0.columns],
                    data=dfv_0.to_dict('results'),
                       ),
                dcc.Link(html.Button('ADD REPAIR', id='add_repair', n_clicks=0), href='/add_repair/{}/{}'.format(username, vin), refresh=False),            
                       ])]),
    elif len(dfv1) == 0 and len(dfv) != 0:
        return html.Table(children=[
            dbc.Container([
                dbc.Label('Vehicle Repair history and need Add Repair for this action'),
                html.Br(),
                dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in dfv.columns],
                    data=dfv.to_dict('results'),),
                dcc.Link(html.Button('ADD REPAIR', id='add_repair', n_clicks=0), href='/add_repair/{}/{}'.format(username, vin), refresh=False), ])])
    elif len(dfv1) != 0:
        customerid = dfv1["CustomerID"].values[0]
        start_date = dfv1["Start_date"].values[0]
        return html.Table(children=[
            dbc.Container([
                dbc.Label('Vehicle is reparing, Please Update Repair'),
                html.Br(),
                dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in dfv1.columns],
                    data=dfv1.to_dict('results'),
                       ),
               dcc.Link(html.Button('UPDATE REPAIR', id='update_repiar', n_clicks=0),href='/update_repair/{}/{}/{}/{}'.format(username, vin, start_date, customerid), refresh=False),
])])


def add_repair_layout(vin, username):
    add_repair_layout=html.Div([
    html.Div([dcc.Link(html.Button('Log Out'), href='/'),
                 dcc.Link(html.Button('Return to Service Witer Portal'), href='/logged_in_service_writer/{}'.format(username)),
           ]),
	html.H1("ADD REPAIR FORM"),
	html.Div([
		html.Label('Vehicle VIN: {}'.format(vin)),
	]),
	html.Br(),
	html.Div([
		html.Label('Customer Type'),		
		dcc.RadioItems(
			id='customer_type',
    		options=[
        	{'label': 'Individual Customer', 'value': 'IC'},
        	{'label': 'Business', 'value': 'BUS'},
    		],
    		value='IC'
			),
		]),
	html.Br(), html.Br(),
	html.Label('Individual Person Id'),
	dcc.Input(id='ip_id'),
	html.Label('Business Tax Id'),
	dcc.Input(id='tax_id'), html.Br(), html.Br(),
	html.Button(id='query-customer', n_clicks=0, children='Query Customer ID'),
	html.Div(id='output_coustomer_table'),html.Br(),html.Br(),
	html.Div([
		html.Label('CustomerID'),
		dcc.Input(id='customerID', type='number'),
	]),
    html.Br(),	
    html.Div([
		html.Label('Odometer'),
		dcc.Input(id='odometer', type='number'),
	]),
    html.Div([
        html.Label('Description'),
        dcc.Input(id='description', type='text')
    ]),
    html.Div([html.Label('Start Date'),
                dcc.DatePickerSingle(
                    id='startdate',
                    disabled=True,
                    max_date_allowed=date.today(),
                    date=date.today(),
                    display_format='Y-M-D'),]),
    html.Br(),
	html.Div([html.Button('ADD REPAIR', id='add_repair', n_clicks=0),
             dcc.Link(html.Button('CANCEL', id='cancel', n_clicks=0), href='/repair_form_main_page/{}'.format(username),refresh=False),
            ]), 
    html.Div(id='output_add_repair_table'),
    html.Div(id='jump-to-add-labor-parts')
    ])
    return add_repair_layout

@app.callback(
dash.dependencies.Output('output_coustomer_table', 'children'),
[dash.dependencies.Input('query-customer', 'n_clicks')],
State('customer_type','value'),
State('ip_id','value'),
State('tax_id','value'),
State('url', 'pathname'),
)
def customer_repair(n_clicks,customer_type, ip_id, tax_id, pathname):
    username = pathname.split('/')[-2]
    vin = pathname.split('/')[-1]
    if n_clicks == 0:
        return
    if customer_type == 'IC':
        # A0536865675
        dfc_i=pd.read_sql("SELECT c.CustomerID, c.Email, ip.ID, ip.Fname, \
            ip.Lname FROM Customer As c NATURAL JOIN IndividualPerson AS ip WHERE ip.ID= %s", mydb, params=(ip_id,))
        if(dfc_i.empty): 
            return html.Div(dcc.Link('No customer found. Click to add customer.', href='/add_customer_ip/{}/{}/{}'.format(username, vin, ip_id)))
        else:
            return  html.Table(children=[
                dbc.Container([
                    dbc.Label('Customer Profile'),
                    html.Br(),
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name": i, "id": i} for i in dfc_i.columns],
                        data=dfc_i.to_dict('records'))
                            ])
                    ])
    if customer_type == 'BUS':
        # 09-5111889
        dfc_b=pd.read_sql("SELECT c.CustomerID, c.Email, ip.ID, ip.Fname, \
            ip.Lname FROM Customer As c NATURAL JOIN IndividualPerson AS ip WHERE ip.CustomerID= %s", mydb, params=(tax_id,))
        if(dfc_b.empty): 
            return html.Div(dcc.Link('No customer found. Click to add customer.', href='/add_customer_b/{}/{}/{}'.format(username, vin, tax_id)))
        else:
            return  html.Table(children=[
                dbc.Container([
                    dbc.Label('Customer Profile'),
                    html.Br(),
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name": i, "id": i} for i in dfc_b.columns],
                        data=dfc_b.to_dict('records'))
                            ])
                    ])

@app.callback(
Output('output_add_repair_table','children'),
[Input('add_repair','n_clicks')],
State('customerID','value'),
State('odometer','value'),
State('description', 'value'),
State('startdate','date'),
State('url', 'pathname'),
)
def add_repair(n_clicks, customerID, odometer, description, start_date, pathname):
    if n_clicks == 0:
        return
    vin_value = pathname.split('/')[-1]
    username = pathname.split('/')[-2]

    dict_temp = {"CustomerID":customerID, "Odometer":odometer}
    for key, val in dict_temp.items():
        if val is None:
            return " {} Field can not be Empty".format(key)
    
    df_c_c=pd.read_sql("SELECT CustomerID FROM Customer WHERE CustomerID=%s", mydb, params=(customerID,))
    if len(df_c_c) == 0:
        return "CustomerID {} not exist".format(customerID)

    if int(n_clicks)>0 :
        if description is None:
            query_temp = "INSERT INTO Repair (VIN, CustomerID, Start_date, Odometer, Username) VALUES \
                ('%s','%s', '%s', '%s', '%s')" % (vin_value, customerID, start_date, odometer, username)
        else:
            query_temp = "INSERT INTO Repair (VIN, CustomerID, Start_date, Odometer, Description, Username) VALUES \
                ('%s','%s', '%s', '%s', '%s', '%s')" % (vin_value, customerID, start_date, odometer, description, username)
        try:
            cursor.execute(query_temp)
        except:
            return "One customer cannot repair one vehicle at the same day !!!"
        mydb.commit()
        df_repair_update = pd.read_sql("SELECT r.VIN, r.CustomerID, r.Start_date, r.Odometer, r.Username \
            FROM Repair as r WHERE r.vin=%s and r.Start_date=%s and r.CustomerID=%s ", mydb, params=(vin_value, start_date, customerID))
        return html.Table(children=[
                dbc.Container([
                    dbc.Label('Add Repair Sucessfully'),
                    html.Br(),
                    dash_table.DataTable(
                    id = 'output_add_repair_table',
                    columns=[{"name": i, "id": i} for i in df_repair_update.columns],
                    data=df_repair_update.to_dict('records'),
                        ),
                    dcc.Location(href='/add_laborfee_part/{}/{}/{}/{}'.format(username, vin_value, start_date, customerID), id='add_labor_parts_page')
                    ])])

def add_laborfee_parts_layout(username, vin_value, customerID, start_date):
    add_laborfee_parts_layout = html.Div([
        dcc.Link(html.Button('Log Out'), href='/'),
        dcc.Link(html.Button('Return to Service Witer Portal'), href='/logged_in_service_writer/{}'.format(username)),
        html.H2("ADD Labor fee and parts as need"),
        html.Div(id='output_add_repair_table'), 
        html.Br(), html.Br(),
        html.Label('Labor fee'),
        daq.NumericInput(id='labor_fee', value=0,size=100, max=sys.maxsize),
        html.Div([
        html.Label('Vendor Name'),
        dcc.Input(id='vendor_name', type='text'),
    ]),

        html.Div([
            html.Label('Part Number'),
            dcc.Input(id='part_number', type='text'),
    ]),
        html.Div([
            html.Label('Part Price'),
            dcc.Input(id='part_price', type='number'),
    ]),
        html.Div([
            html.Label('Part Quantity'),
            dcc.Input(id='part_qty', type='number'),
    ]),
    html.Br(),
    html.Br(),
        html.Div([html.Button('ADD', id='add-laborfee-part', n_clicks=0),
             dcc.Link(html.Button('CANCEL', id='cancel', n_clicks=0), href='/repair_form_main_page/{}'.format(username),refresh=False),
            ]),
        html.Div(id='output_add_part_table'),
        html.Div(id='return-to-repair-main-l'),   
           ])
    return add_laborfee_parts_layout

@app.callback(
Output('output_add_part_table','children'),
Input('add-laborfee-part','n_clicks'),
State('url','pathname'),
State('labor_fee', 'value'),
State('vendor_name','value'),
State('part_number','value'),
State('part_price','value'),
State('part_qty','value'),
)
def add_laborfee_part(n_clicks, pathname, labor_fee, vendor_name, part_number, part_price, part_qty):
    customerID = pathname.split('/')[-1]
    start_date = pathname.split('/')[-2]
    vin_value = pathname.split('/')[-3]
    username = pathname.split('/')[-4]
    if n_clicks == 0:
        return
    query_temp="UPDATE Repair SET Labor_fee=%s WHERE VIN='%s' and CustomerID='%s' and Start_date='%s'" %(labor_fee,vin_value,customerID,start_date)
    cursor.execute(query_temp)
    mydb.commit()
    if part_number is not None:
        query_temp_part = "INSERT INTO Part (VIN, CustomerID, Start_date, Vendor_name, Part_price, Part_number, Quantity) VALUES \
        ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (vin_value, customerID, start_date, vendor_name, part_price, part_number, part_qty)
        cursor.execute(query_temp_part)
        mydb.commit()
    df_part_table = pd.read_sql("SELECT r.VIN, r.CustomerID, r.Start_date, r.Labor_fee, r.Odometer, \
        p.Vendor_name, p.Part_price * p.Quantity AS Part_total_price, p.Part_number \
        FROM Repair as r Inner Join Part as p \
            WHERE r.vin=%s and r.Start_date=%s and p.Vendor_name=%s and p.Part_number=%s and r.CustomerID=%s ", mydb, params=(vin_value, start_date,vendor_name, part_number, customerID))

    return html.Table(children=[
                dbc.Container([
                    dbc.Label('Add labor fee and Part Sucessfully'),
                    html.Br(),
                    dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df_part_table.columns],
                    data=df_part_table.to_dict('records'),
                        )]),
                    dcc.ConfirmDialog(id='confirm-laborfee-parts-dialog', 
                                      message='This is to confirm you\'ve Add this labor fee and parts! Click any button to return to repair main page!', displayed=False)   ])

@app.callback(dash.dependencies.Output('confirm-laborfee-parts-dialog', 'displayed'),
[dash.dependencies.Input('output_add_part_table', 'children')])
def confirm_repair(content):
    if content != "":
        return True
    else:
        return False

@app.callback(dash.dependencies.Output('return-to-repair-main-l', 'children'),
[dash.dependencies.Input('confirm-laborfee-parts-dialog', 'submit_n_clicks'),
dash.dependencies.Input('confirm-laborfee-parts-dialog', 'cancel_n_clicks')],
State('url', 'pathname'))
def return_to_repair_main(snc, cnc, pathname):
    uname = pathname.split('/')[-4]
    if snc or cnc:
        return dcc.Location(href='/repair_form_main_page/' + uname, id='repair_main_page')

def update_repair_layout(username, vin, start_date, customerID):
    update_repair_layout=html.Div([
    html.Div([dcc.Link(html.Button('Log Out'), href='/'),
                 dcc.Link(html.Button('Return to Service Witer Portal'), href='/logged_in_service_writer/{}'.format(username)),
           ]),
	html.H1("UPDATE REPAIR FORM"),
	html.Div([
		html.Label('Vehicle VIN: {}'.format(vin)),
	]),
	html.Br(),
	html.Div([
        html.Label('CustomerID: {}'.format(customerID)),
	]),
    html.Div([
        html.Label('Start Date: {}'.format(start_date)),
	]),
	html.Br(), html.Hr(), html.Br(),
    html.Div([
		html.Label('Labor Fee'),
        daq.NumericInput(id='labor_fee', value=0,size=100, max=sys.maxsize),
	]),
	html.Div([html.Button('UPDATE LABOR FEE', id='update_repair', n_clicks=0),
            dcc.Link(html.Button('CANCEL', id='cancel', n_clicks=0), href='/repair_form_main_page/{}'.format(username),refresh=False),

            ]),
    html.Div(id='output_update_repair_table'),  
    
    html.Br(), html.Hr(), html.Br(),
    html.Div([
        html.Label('Vendor Name'),
        dcc.Input(id='vendor_name', type='text'),
    ]),
        html.Div([
        html.Label('Part Number'),
        dcc.Input(id='part_number', type='text'),
    ]),
    html.Div([
        html.Label('Part Price'),
        dcc.Input(id='part_price', type='number'),
    ]),
    html.Div([
        html.Label('Part Quantity'),
        dcc.Input(id='part_qty', type='number'),
    ]),

    html.Div([html.Button('UPDATE PART', id='add_part', n_clicks=0),
            dcc.Link(html.Button('CANCEL', id='cancel', n_clicks=0), href='/repair_form_main_page/{}'.format(username),refresh=False),

            ]),
	html.Div(id='output_add_part_table_2'),
	html.Br(), html.Hr(), html.Br(),
	html.Label('fill out customerid, start_date'),
	html.Br(),
	html.Button('COMPLETE REPAIR', id='complete_repair', n_clicks=0),
	html.Div(id='output_complete_repair_table'),
    html.Div(id='return-to-repair-main'),
	])
    return update_repair_layout


@app.callback(
Output('output_update_repair_table','children'),
Input('update_repair','n_clicks'),
State('url','pathname'),
State('labor_fee','value'),
)
def update_repair(n_clicks, pathname, laborfee):
    vin_value = pathname.split('/')[-3]
    start_date = pathname.split('/')[-2]
    customerID = pathname.split('/')[-1]
    username = pathname.split('/')[-4]
    if int(n_clicks)>0 :
        df_labor_fee = pd.read_sql("SELECT r.Labor_fee FROM Repair as r WHERE r.vin=%s and r.Start_date=%s and r.CustomerID=%s ", mydb, params=(vin_value, start_date, customerID))
        if df_labor_fee.iloc[0, 0] is None:
            labor_fee_threshod = 0
        else:
            labor_fee_threshod = df_labor_fee.iloc[0, 0]
        if float(laborfee) < labor_fee_threshod and username != "roland":
            return "labor fee is lower than previous labor fee"
        query_temp="UPDATE Repair SET Labor_fee=%s WHERE VIN='%s' and CustomerID='%s' and Start_date='%s'" %(laborfee,vin_value,customerID,start_date)
        cursor.execute(query_temp)
        mydb.commit()
        df_repair_update = pd.read_sql("SELECT r.VIN, r.CustomerID, r.Start_date, r.Labor_fee, r.Odometer, r.Username \
            FROM Repair as r WHERE r.vin=%s and r.Start_date=%s and r.CustomerID=%s ", mydb, params=(vin_value, start_date, customerID))
        return html.Table(children=[
                dbc.Container([
                    dbc.Label('Update Repair Sucessfully'),
                    html.Br(),
                    dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df_repair_update.columns],
                    data=df_repair_update.to_dict('records'),
                        )])])

@app.callback(
Output('output_add_part_table_2','children'),
Input('add_part','n_clicks'),
State('url','pathname'),
State('labor_fee', 'value'),
State('vendor_name','value'),
State('part_number','value'),
State('part_price','value'),
State('part_qty','value'),
)
def add_part(n_clicks, pathname, labor_fee, vendor_name, part_number, part_price, part_qty):
    customerID = pathname.split('/')[-1]
    start_date = pathname.split('/')[-2]
    vin_value = pathname.split('/')[-3]
    username = pathname.split('/')[-4]
    if n_clicks == 0:
        return
    dict_temp = {"Vendor Name":vendor_name, "Part Number":part_number, "Part Price":part_price, "Part Quantity": part_qty}
    for key, val in dict_temp.items():
        if val is None:
            return " {} Field can not be Empty".format(key)
    insert_temp_part = "INSERT INTO Part (VIN, CustomerID, Start_date, Vendor_name, Part_price, Part_number, Quantity) VALUES \
        ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (vin_value, customerID, start_date, vendor_name, part_price, part_number, part_qty)
    cursor.execute(insert_temp_part)
    mydb.commit()
    df_part_table = pd.read_sql("SELECT r.VIN, r.CustomerID, r.Start_date, r.Labor_fee, r.Odometer, \
        p.Vendor_name, p.Part_price * p.Quantity AS Part_total_price, p.Part_number \
        FROM Repair as r Inner Join Part as p \
            WHERE r.vin=%s and r.Start_date=%s and p.Vendor_name=%s and p.Part_number=%s and r.CustomerID=%s ", mydb, params=(vin_value, start_date,vendor_name, part_number, customerID))

    return html.Table(children=[
                dbc.Container([
                    dbc.Label('Add Part Sucessfully'),
                    html.Br(),
                    dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df_part_table.columns],
                    data=df_part_table.to_dict('records'),
                        )]),
                    ])

@app.callback(
Output('output_complete_repair_table','children'),
Input('complete_repair','n_clicks'),
State('url','pathname'),
)
def complete_repair(n_clicks, pathname):
    customerID = pathname.split('/')[-1]
    start_date = pathname.split('/')[-2]
    vin_value = pathname.split('/')[-3]
    username = pathname.split('/')[-4]
    if n_clicks == 0:
        return
    get_current_date = datetime.today().strftime('%Y-%m-%d')
    query_temp="UPDATE Repair SET Complete_date='%s' WHERE VIN='%s' and CustomerID='%s' and Start_date='%s'" %(get_current_date, vin_value, customerID, start_date)
    cursor.execute(query_temp)
    mydb.commit()
    df_repair_update = pd.read_sql("SELECT r.VIN, r.CustomerID, r.Start_date, r.Labor_fee, r.Complete_date \
        FROM Repair as r WHERE r.vin=%s and r.Start_date=%s and r.CustomerID=%s ", mydb, params=(vin_value, start_date, customerID))
    return html.Div([html.Table(children=[
                dbc.Container([
                    dbc.Label('Thank you, Your repair has been completed'),
                    html.Br(),
                    dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in df_repair_update.columns],
                    data=df_repair_update.to_dict('records'),
                        ),
                    dcc.ConfirmDialog(id='confirm-repair-dialog', 
                                      message='This is to confirm you\'ve complete this repair! Click any button to return to repair main page!', displayed=False)   
                        ])])])

@app.callback(dash.dependencies.Output('confirm-repair-dialog', 'displayed'),
[dash.dependencies.Input('output_complete_repair_table', 'children')])
def confirm_repair(content):
    if content != "":
        return True
    else:
        return False

@app.callback(dash.dependencies.Output('return-to-repair-main', 'children'),
[dash.dependencies.Input('confirm-repair-dialog', 'submit_n_clicks'),
dash.dependencies.Input('confirm-repair-dialog', 'cancel_n_clicks')],
State('url', 'pathname'))
def return_to_repair_main(snc, cnc, pathname):
    uname = pathname.split('/')[-4]
    if snc or cnc:
        return dcc.Location(href='/repair_form_main_page/' + uname, id='repair_main_page')


def get_logged_in_manager(uname):
    logged_in_manager = html.Div([
        html.Div([dcc.Link(html.Button('Log Out'), href='/'),
                  dcc.Link(html.Button('Return to Owner Main Menu'), href='/logged_in_admin/' + uname, refresh=True) if uname == "roland" else '',
                  html.H1(children="Welcome to the Jaunty Jalopies Manager Portal!")]),
        html.Br(),
        html.Div([
            "To View Report: ",
            html.Br(),
            html.Br(),
            dcc.Dropdown(
            id='view-report-dropdown',
            options=[
                {'label': 'Sales by Color', 'value': 'SBC'},
                {'label': 'Sales by Type', 'value': 'SBT'},
                {'label': 'Sales by Manufacturer', 'value': 'SBM'},
                {'label': 'Gross Customer Income', 'value': 'GCI'},
                {'label': 'Repairs by Manufacturer/Type/Model', 'value': 'RBMTM'},
                {'label': 'Below Cost Sales', 'value': 'BCS'},
                {'label': 'Average Time in Inventory', 'value': 'ATII'},
                {'label': 'Parts Statistics', 'value': 'PS'},
                {'label': 'Monthly Sales', 'value': 'MS'}
            ],
            style={'width': '50%'},
            value='SBC',
            clearable=False
            ),
            html.Br(),
            html.Button(id='submit-button-view-report', n_clicks=0, children='Submit'),
            html.Div(id='hidden_div_for_redirect_report_callback')
        ]),
        html.Br(),
    html.Br(),
    html.Div([
        html.H3("Search Vehicle"),
        html.Div("Total number of avaliable vehicles: {}".format(get_total_number_of_avaliable_vehicles())),
        html.Br(),
        html.Br(),
        html.Label('VIN'),
        html.Div([dcc.Dropdown(
            id='vin-m',
            options=[
                {'label':i, 'value':i} for i in get_all_vin()['vin'].unique()
            ],
            style={'width': '50%'},
            placeholder = 'Select a vehicle VIN'),]),
        html.Br(),
        html.Br(),
        html.Label('Vehicle Type'),
        html.Div([dcc.Dropdown(
            id='vehicle_type-m',
            options= get_vehicle_type(),
            style={'width': '50%'},
            placeholder = 'Select a vehicle type'),]),
        html.Br(),
        html.Br(),
        html.Label('Vehicle Manufacturer'),
        html.Div([dcc.Dropdown(
            id='vehicle_manufacturer-m',
            options=[
                {'label':i, 'value':i} for i in get_vehicle_manufacturer()['vm'].unique()
            ],
            style={'width': '50%'},
            placeholder = 'Select a manufacturer'),]),
        html.Br(),
        html.Br(),
        html.Label('Year'),
        html.Div([dcc.Dropdown(
            id='vehicle_year-m',
            options=[{'label':x, 'value': x} for x in range(get_model_year(), 1959, -1)],
                placeholder = 'Select a year from current to 1960',
                style={'width': '50%'},
                ),]),
        html.Br(),
        html.Br(),
        html.Label('Color'),
        html.Div([dcc.Dropdown(
            id='vehicle_color-m',
            options=[{'label':i, 'value':i} for i in get_vehicle_color()['vc'].unique()],
            placeholder = 'Select a color'),]),
        html.Br(),
        html.Br(),
        html.Label('List Price'),
        html.Div([
            daq.NumericInput(id='list_price_low_value-m', size=100, max=sys.maxsize, label="lowest value"),
            daq.NumericInput(id='list_price_high_value-m', size=100, max=sys.maxsize, label="highest value")]),
        html.Br(),
        html.Br(),
        html.Label('Keywords'),
        html.Div([dcc.Textarea(id='description-m', placeholder="", style={'width':'80%', 'height': 100}),]),
        html.Br(),
        html.Br(),
        html.Div([
		dcc.RadioItems(
			id='search_sold_type',
    		options=[
        	{'label': 'Unsold Vehicles', 'value': 'UV'},
        	{'label': 'Sold Vehicles', 'value': 'SV'},
            {'label': 'All Vehicles', 'value': 'AV'},
    		],
    		value='AV'
			),
		]),
        html.Button(id='query-search-vehicle-button-m', n_clicks=0, children='Submit'),
        html.Br(),
        html.Br(),
        html.Div(id='output-search-vehicle-table-m')
        ]),
    ])
    return logged_in_manager


@app.callback(
dash.dependencies.Output('hidden_div_for_redirect_report_callback', 'children'),
[dash.dependencies.Input('submit-button-view-report', 'n_clicks')],
[State('view-report-dropdown', 'value'),
 State('url', 'pathname')]

)
def view_report(n_clicks, value, pathname):
    username = pathname.split('/')[-1]
    if n_clicks > 0:
        reporttype = '/view_report_%s/%s' % (value, username)
        return dcc.Location(href=reporttype, id='manager_report')

@app.callback(
dash.dependencies.Output('output-search-vehicle-table-m', 'children'),
[dash.dependencies.Input('query-search-vehicle-button-m', 'n_clicks')],
State('search_sold_type', 'value'),
State('vin-m', 'value'),
State('vehicle_type-m', 'value'),
State('vehicle_manufacturer-m', 'value'),
State('vehicle_year-m', 'value'),
State('vehicle_color-m', 'value'),
State('list_price_low_value-m', 'value'),
State('list_price_high_value-m', 'value'),
State('description-m', 'value'),
)
def query_vehicle_manager(n_clicks, sold_type, vin, vehicle_type, vehicle_manufacturer, vehicle_year, 
                  vehicle_color, list_price_low_value, list_price_high_value, description):
    if n_clicks == 0:
        return
    if description != None:
        description = description.strip()
    value_list = [vin, vehicle_type, vehicle_manufacturer, vehicle_year, 
    vehicle_color, list_price_low_value, list_price_high_value, description]
    if list(set(value_list)) == [None]:
        return "Need input the search condition!"
    name_list = [
                "vin",
                "vehicle_type",
                "vehicle_manufacturer", 
                "vehicle_year",
                "vehicle_color",
                "list_price_low_value",
                "list_price_high_value",
                "description"
                ]
    res = {}
    for i, x in enumerate(value_list):
        if type(x) is tuple:
            x = x[0]
        res[name_list[i]] = str(x)
    value = ()
    if res["description"] == 'None':
        sql = "SELECT v.VIN, v.Type, v.Model_year, v.Manufacturer_name, v.Model_name, \
        GROUP_CONCAT(vc.color) AS Color, \
            v.Invoice_price*1.25 \
                FROM Vehicle AS v INNER JOIN VehicleColor AS vc ON vc.VIN = v.VIN WHERE"
    else:
        sql = "SELECT v.VIN, v.Type, v.Model_year, v.Manufacturer_name, v.Model_name, \
        GROUP_CONCAT(vc.color) AS Color, \
            IF(Description LIKE BINARY %s, 'Yes', 'No') AS 'Match Description or not',\
            v.Invoice_price*1.25 \
                FROM Vehicle AS v INNER JOIN VehicleColor AS vc ON vc.VIN = v.VIN WHERE"
        value += ("%" + res["description"]+ "%",)
    
    if sold_type == "UV":
        sql += " v.Sold_date is NULL "
    if sold_type == "SV":
        sql += " v.Sold_date is not NULL "
    if sold_type == "AV":
        sql += ""
    if res["vin"] != 'None':
        if sql.split(" ")[-1] == 'WHERE':
            sql += " v.Vin = %s "
        else:
            sql += " AND v.Vin = %s "
        value += (res["vin"],)
    if res["vehicle_type"] != 'None':
        if sql.split(" ")[-1] == 'WHERE':
            sql += " v.Type = %s "
        else:
            sql += "AND v.Type = %s "
        value += (res["vehicle_type"],)
    if res["vehicle_manufacturer"] != 'None':
        if sql.split(" ")[-1] == 'WHERE':
            sql += " v.Manufacturer_name = %s "
        else:
            sql += "AND v.Manufacturer_name = %s "
        value += (res["vehicle_manufacturer"],)
    if res["vehicle_year"] != 'None':
        if sql.split(" ")[-1] == 'WHERE':
            sql += " v.Model_year = %s "
        else:
            sql += "AND v.Model_year = %s "
        value += (res["vehicle_year"],)
    if res["vehicle_color"] != 'None':
        if sql.split(" ")[-1] == 'WHERE':
            sql += " vc.Color in (%s) "
        else:
            sql += "AND vc.Color in (%s) "
        value += (res["vehicle_color"],)
    if res["list_price_low_value"] != 'None' and res["list_price_high_value"] != 'None':
        if sql.split(" ")[-1] == 'WHERE':
            sql += " v.Invoice_price BETWEEN %s/1.25 AND %s/1.25 "
        else:
            sql += "AND v.Invoice_price BETWEEN %s/1.25 AND %s/1.25 "
        value += (res["list_price_low_value"], res["list_price_high_value"],)
    if res["list_price_low_value"] == 'None' and res["list_price_high_value"] != 'None':
        if sql.split(" ")[-1] == 'WHERE':
            sql += " v.Invoice_price <= %s/1.25 "
        else:
            sql += "AND v.Invoice_price <= %s/1.25 "
        value += (res["list_price_high_value"],)
    if res["list_price_low_value"] != 'None' and res["list_price_high_value"] == 'None':
        if sql.split(" ")[-1] == 'WHERE':
            sql += " v.Invoice_price >= %s/1.25 "
        else:    
            sql += "AND v.Invoice_price >= %s/1.25 "
        value += (res["list_price_low_value"],)
    if res["description"] != 'None':
        if sql.split(" ")[-1] == 'WHERE':
            sql += " ( v.Manufacturer_name LIKE BINARY %s OR v.Model_year LIKE BINARY %s OR v.Model_name LIKE BINARY %s OR v.Description LIKE BINARY %s) "
        else:
            sql += "AND ( v.Manufacturer_name LIKE BINARY %s OR v.Model_year LIKE BINARY %s OR v.Model_name LIKE BINARY %s OR v.Description LIKE BINARY %s) "
        value += ("%" + res["description"]+ "%","%" + res["description"]+ "%", "%" + res["description"]+ "%", "%" + res["description"]+ "%",)
    
    sql += "GROUP BY v.VIN ORDER BY v.VIN ASC"

    output = CONN.query(sql, value)

    if len(output) == 0:
        return "Sorry, it looks like we don’t have that in stock!"
   
    if res["description"] == 'None':
        df = pd.DataFrame(output, columns=["VIN", "Type", "Model_year", 
                                   "Manufacturer_name", "Model_name", "Color",
                                   "Price"])
        df['Price'] = df['Price'].apply(lambda x: round(x, 2))
        df["VIN"] = "[" + df["VIN"] + "](/logged_in_manager/view_vehicle_detail/" + df["VIN"] + ")"
        return html.Table(children=[
            dbc.Container([
                dbc.Label('Results'),
                html.Br(),
                dash_table.DataTable(
                    columns=[{"name": "VIN", "id": "VIN", "type": "text", "presentation": "markdown"}, {"name": "Type", "id": "Type"}, {"name": "Model_year", "id": "Model_year"}, {"name": "Manufacturer_name", "id": "Manufacturer_name"}, {"name": "Model_name", "id": "Model_name"}, {"name": "Color", "id": "Color"}, {"name": "Price", "id": "Price"}],
                    data=df.to_dict('results'),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="single",
                       )])])
    else:
        df = pd.DataFrame(output, columns=["VIN", "Type", "Model_year", 
                                   "Manufacturer_name", "Model_name", "Color",
                                   "Match Description", "Price"])
        df['Price'] = df['Price'].apply(lambda x: round(x, 2))
        df["VIN"] = "[" + df["VIN"] + "](/logged_in_sales/view_vehicle_detail/" + df["VIN"] + ")"
        return html.Table(children=[
            dbc.Container([
                dbc.Label('Results'),
                html.Br(),
                dash_table.DataTable(
                    columns=[{"name": "VIN", "id": "VIN", "type": "text", "presentation": "markdown"}, {"name": "Type", "id": "Type"}, {"name": "Model_year", "id": "Model_year"}, {"name": "Manufacturer_name", "id": "Manufacturer_name"}, {"name": "Model_name", "id": "Model_name"}, {"name": "Color", "id": "Color"}, {"name": "Match Description", "id": "Match Description"}, {"name": "Price", "id": "Price"}],
                    data=df.to_dict('results'),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="single",
                       )])])


logged_in_admin = html.Div([
    html.Div([dcc.Link(html.Button('Log Out'), href='/'),
    html.H1(children="Welcome to the Jaunty Jalopies Admin Portal!")]),
    html.Br(),
    html.Div([
        "To Search Vehicle: ",
        dcc.Link(html.Button('Search Vehicle'), href='/')
    ]),
    html.Br(),
    html.Div([
        "To Open A Repair Form: ",
        dcc.Link(html.Button('Open Repair Form'), href='/')
    ]),
    html.Br(),
    html.Div([
        "To Add Vehicle: ",
        dcc.Link(html.Button('Add Vehicle'), href='/')
    ]),
    html.Br(),
    html.Div([
        "To View Report: ",
        dcc.Link(html.Button('View Report'), href='/')
    ])
])

# inventory clerk start
class AddVehicle():

    def __init__(self) -> None:
        config = Config.dbinfo().copy()
        self.conn = DBConnector(config['user'], config['password'], config['database'])

    def VIN_not_exist(self, VIN, input_vin):
        sql = "SELECT VIN FROM Vehicle"
        VINs = self.conn.simple_query(sql)
        for vin in VINs:
            if vin[0] == VIN and VIN != input_vin: return False
        return True

    def check_model_year(self, model_year):
        return model_year.isnumeric() and len(model_year) == 4 \
               and int(model_year) <= int(datetime.today().year) + 1

    def get_manufacturer(self):
        sql = "SELECT Manufacturer_name FROM Manufacturer"
        manufacturers = self.conn.simple_query(sql)
        res = []
        for manufacturer in manufacturers:
            res.append(manufacturer[0])
        return res

    def check_invoice_price(self, invoice_price):
        try:
            if float(invoice_price) > 0:
                return True
            else:
                return False
        except ValueError:
            return False

    def get_Add_date(self):
        return datetime.today().strftime("%Y-%m-%d")

    def get_vehicle_type(self):
        vehicle_types = [
            {"label": "Car", "value": "Car"},
            {"label": "Convertible", "value": "Convertible"},
            {"label": "SUV", "value": "SUV"},
            {"label": "Van/MiniVan", "value": "VanMinivan"},
            {"label": "Truck", "value": "Truck"}
        ]
        return vehicle_types

    def save_vehicle(self, value):
        sql = "INSERT INTO Vehicle (VIN, Manufacturer_name, Model_name, Model_year, Invoice_price, Description," \
              "Add_date, Type, Added_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = value
        self.conn.insert(sql, val)

    def save_colors(self, value):
        sql = "INSERT INTO VehicleColor (VIN, Color) VALUES (%s, %s)"
        val = value
        self.conn.insert(sql, val)

    def save_Car(self, value):
        sql = "INSERT INTO Car (VIN, Num_of_doors) VALUES (%s, %s)"
        val = value
        self.conn.insert(sql, val)

    def save_Convertible(self, value):
        sql = "INSERT INTO Convertible (VIN, Roof_type, Back_seat_count) VALUES (%s, %s, %s)"
        val = value
        self.conn.insert(sql, val)

    def save_SUV(self, value):
        sql = "INSERT INTO SUV (VIN, Drivetrain_type, Num_of_cupholders) VALUES (%s, %s, %s)"
        val = value
        self.conn.insert(sql, val)

    def save_Truck(self, value):
        sql = "INSERT INTO Truck (VIN, Cargo_capacity, Num_of_rear_axies, Cargo_cover_type) VALUES (%s, %s, %s, %s)"
        val = value
        self.conn.insert(sql, val)

    def save_VanMinivan(self, value):
        sql = "INSERT INTO VanMinivan (VIN, Has_back_door) VALUES (%s, %s)"
        val = value
        self.conn.insert(sql, val)

    def get_VIN(self, vin):
        sql = "SELECT VIN FROM Vehicle WHERE VIN = %s"
        val = (vin,)
        return self.conn.query(sql, val)

    def get_vehicle_for_update(self, vin):
        sql = "SELECT VIN, Manufacturer_name, Model_name, Model_year, Invoice_price, Description, Add_date, Added_by FROM Vehicle WHERE VIN = %s"
        val = (vin,)
        output = self.conn.query(sql, val)
        res = []
        for val in output[0]:
            res.append(str(val))
        return res

    def get_vehicle_for_show(self, vin):
        sql = "SELECT VIN, Manufacturer_name, Model_name, Model_year, Invoice_price, Description, Add_date, Type, Added_by FROM Vehicle WHERE VIN = %s"
        val = (vin,)
        output = self.conn.query(sql, val)
        res = []
        for val in output[0]:
            res.append(str(val))
        return res

    def get_Car(self, vin):
        sql = "SELECT Num_of_doors FROM Car WHERE VIN = %s"
        val = (vin,)
        output = self.conn.query(sql, val)
        res = []
        if not output:
            return res
        for val in output[0]:
            res.append(str(val))
        return res

    def get_Convertible(self, vin):
        sql = "SELECT Roof_type, Back_seat_count FROM Convertible WHERE VIN = %s"
        val = (vin,)
        output = self.conn.query(sql, val)
        res = []
        if not output:
            return res
        for val in output[0]:
            res.append(str(val))
        return res

    def get_SUV(self, vin):
        sql = "SELECT Drivetrain_type, Num_of_cupholders FROM SUV WHERE VIN = %s"
        val = (vin,)
        output = self.conn.query(sql, val)
        res = []
        if not output:
            return res
        for val in output[0]:
            res.append(str(val))
        return res

    def get_VanMinivan(self, vin):
        sql = "SELECT Has_back_door FROM VanMinivan WHERE VIN = %s"
        val = (vin,)
        output = self.conn.query(sql, val)
        res = []
        if not output:
            return res
        for val in output[0]:
            res.append(str(val))
        return res

    def get_Truck(self, vin):
        sql = "SELECT Cargo_capacity, Num_of_rear_axies, Cargo_cover_type FROM Truck WHERE VIN = %s"
        val = (vin,)
        output = self.conn.query(sql, val)
        res = []
        if not output:
            return res
        for val in output[0]:
            res.append(str(val))
        return res

    def call_get_type_details_method(self, type, vin):
        if type == 'Car':
            return self.get_Car(vin)
        if type == 'Convertible':
            return self.get_Convertible(vin)
        if type == 'SUV':
            return self.get_SUV(vin)
        if type == 'VanMinivan':
            return self.get_VanMinivan(vin)
        if type == 'Truck':
            return self.get_Truck(vin)

    def get_colors(self, vin):
        sql = "SELECT Color FROM VehicleColor WHERE VIN = %s"
        val = (vin,)
        output = self.conn.query(sql, val)
        res = []
        for val in output:
            res.append(str(val[0]))
        return res

    def update_vehicle(self, attributes, vin):
        atts = ""
        values = ()
        n = len(attributes)
        for k, val in attributes:
            atts = k + " = %s, "
            values.append(val)
        values.append(vin)
        sql = "UPDATE Vehicle SET " + atts + " WHERE VIN = %s"
        # values contains all new values and vin
        self.conn.insert(sql, values)

    def call_save_type_method(self, type, value):
        if type == 'Car':
            self.save_Car(value)
        elif type == 'Convertible':
            self.save_Convertible(value)
        elif type == 'SUV':
            self.save_SUV(value)
        elif type == 'VanMinivan':
            self.save_VanMinivan(value)
        elif type == 'Truck':
            self.save_Truck(value)

add_vehicle = AddVehicle()
# manufacturers = add_vehicle.get_manufacturer()
colors = ["Aluminum", "Beige", "Black", "Blue", "Brown", "Bronze", "Claret", "Copper", "Cream", "Gold", "Gray", "Green",
          "Maroon", "Metallic", "Navy", "Orange", "Pink", "Purple", "Red", "Rose", "Rust", "Silver", "Tan", "Turquoise",
          "White", "Yellow"]
vehicle_types = add_vehicle.get_vehicle_type()
input_vehicle_values = {
    'VIN': "",
    'manufacturer': "",
    'model_name': "",
    'model_year': "",
    'invoice_price': "",
    'description': "",
    'add_date': str(add_vehicle.get_Add_date()),
    'vehicle_type': "",
    'added_by': "",
}
no_required_attributes = ['customerID', 'sold_date', 'sold_price', 'username']
required_attributes = ['VIN', 'manufacturer', 'model_name', 'model_year', 'invoice_price', 'description', 'add_date',
                       'vehicle_type']
select_colors = {'colors': []}
input_type_values = {
    'Car': {'num_of_doors': ''},
    'Convertible': {'roof_type': '',
                    'back_seat_count': ''},
    'SUV': {'drivetrain_type': '',
            'num_of_cupholders': ''},
    'VanMinivan': {'has_back_door': ''},
    'Truck': {'cargo_capacity': '',
              'num_of_rear_axles': '',
              'cargo_cover_type': '',
              },
}

def get_inventory_clerk_layout(uname, passw):
    logged_in_inventory_clerk = html.Div([
        html.Div([dcc.Link(html.Button('Log Out'), href='/'),
                  dcc.Link(html.Button('Return to Owner Main Menu'), href='/logged_in_admin/' + uname,
                           refresh=True) if uname == "roland" else '',
                  html.H1(children="Welcome to the Jaunty Jalopies Inventory Clerk Portal!")]),
        html.Br(),
        html.Div([
            "To Add Vehicle: ",
            dcc.Link(html.Button(id='add-vehicle', children='Add Vehicle', n_clicks=0),
                     href='/add_vehicle/%s/%s' % (uname, passw), refresh=False),
        ])
    ])
    return logged_in_inventory_clerk

def add_or_update_vehicle(uname, passw):
    input_vehicle_values['added_by'] = uname
    title = 'Add Vehicle'
    for k in input_vehicle_values.keys():
        if k != "add_date" and k != "added_by":
            input_vehicle_values[k] = ""
    select_colors['colors'] = []
    next_year = int(datetime.today().year) + 1
    add_vehicle_layout = html.Div([
        html.H1(title),
        html.Hr(), html.Br(),
        html.Div([
            "VIN: ",
            dcc.Input(
                id='VIN',
                placeholder="Input VIN",
                style={'width': '20%'},
                value=input_vehicle_values["VIN"],
            ),
            html.Div(id='VIN-error', style={'color': 'red'})
        ]),
        html.Br(),
        html.Div([
            "Model Name: ",
            dcc.Input(
                id='model-name',
                placeholder='Input model name',
                style={'width': '20%'},
                value=input_vehicle_values["model_name"]
            ),
            html.Div(id='model-name-placeholder')
        ]),
        html.Br(),
        html.Div([
            'Model Year: ',
            dcc.Dropdown(
                id='model-year',
                options=[{'label': x, 'value': x} for x in range(next_year, 1959, -1)],
                placeholder='Select from 1960 to the next year',
                style={'width': '50%'},
                clearable=False,
            ),
            html.Div(id='model-year-placeholder'),
        ]),
        html.Br(),
        html.Div([
            "Manufacturer: ",
            dcc.Dropdown(
                id='manufacturer',
                options=[{'label': m, 'value': m} for m in add_vehicle.get_manufacturer()],
                clearable=False,
                placeholder='Select a manufacturer',
                style={'width': '50%'},
                value=input_vehicle_values["manufacturer"]
            ),
            html.Div(id='manufacturer-placeholder', style={'display': 'none'})
        ]),
        html.Br(),
        html.Div([
            'Color: ',
            html.Button('Add Color', id='add-color', n_clicks=0),
            html.Button('Delete Color', id='delete-color', n_clicks=0),
            html.Div(id='dropdown-container', children=[]),
            html.Div(id='dropdown-container-output', style={'display': 'none'}),
            html.Div(id='color-error', style={'color': 'red'})
        ]),
        html.Br(),
        html.Div([
            'Invoice Price: ',
            dcc.Input(
                id='invoice-price',
                placeholder='Input invoice price',
                style={'width': '20%'},
                value=input_vehicle_values["invoice_price"],
                type='number'
            ),
            html.Div(id='invoice-price-error', style={'color': 'red'})
        ]),
        html.Br(),
        html.Div([
            'Description:',
            html.Div(
                dcc.Textarea(
                    id='description',
                    placeholder='Optional',
                    style={'width': '80%', 'height': 100},
                    value=input_vehicle_values["description"]
                ),
            ),
            html.Div(id='description-placeholder')
        ]),
        html.Br(),
        html.Div([
            'Vehicle Type: ',
            dcc.Dropdown(
                id='vehicle_type',
                options=add_vehicle.get_vehicle_type(),
                clearable=False,
                placeholder='Select vehicle type',
                style={'width': '50%'},
                value=input_vehicle_values["vehicle_type"]
            ),
            html.Div(id='type-placeholder')
        ]),
        html.Br(),
        html.Div(
            'Add Date: {}'.format(input_vehicle_values['add_date']),
        ),
        html.Br(),
        html.Div(
            'Added By: {}'.format(input_vehicle_values['added_by']),
        ),
        html.Hr(),
        html.Br(),
        html.Div([
            html.Button(id='save', children='SAVE', n_clicks=0),
            dcc.Link(html.Button(id='next', children='NEXT', n_clicks=0, hidden=True, style={'color': 'green'}),
                     href='/add_type_details/%s/%s' % (uname, passw),
                     refresh=False),
            dcc.Link(html.Button(id='return-index', children='RETURN', n_clicks=0), href='/logged_in_inventory_clerk/%s/%s' % (uname, passw), refresh=False),
        ], style={'text-align': 'center'}),
        html.Div(id='errors',style={'color': 'red'}),
    ])
    return add_vehicle_layout

def layout_vehicle_type_details(vt, uname, passw):
    for vals in input_type_values.values():
        for k in vals:
            vals[k] = ''
    vehicle_type_layout = html.Div([
        html.H1('Add ' + vt + ':'),
        html.Hr(), html.Br(),
        html.Div(id='type-placeholder', children=vt, style={'display': 'none'}),
        html.Div(id='vehicle-type-details', children=vehicle_type_details[vt]),
        html.Hr(),
        html.Br(),
        html.Div([
            html.Button(id='save-vehicle-type-details', children='SAVE'),
            dcc.Link(html.Button(id='show-details', children='Show Vehicle Details', n_clicks=0, hidden=True,
                                 style={'color': 'green'}), href='/inventory_clerk/show_details/%s/%s/%s' % (input_vehicle_values['VIN'], uname, passw),
                     refresh=False),
            dcc.Link(html.Button(id='return-from-type', children='RETURN', n_clicks=0, hidden=True), href='/logged_in_inventory_clerk/%s/%s' % (uname, passw), refresh=False),
        ], style={'text-align': 'center'}),
        html.Div(id='details_errors', style={'color': 'red'}),
    ])
    return vehicle_type_layout

@app.callback(
    Output('VIN-error', 'children'),
    Input('VIN', 'value'),
    State('url', 'pathname')
)
def input_VIN(value, pathname):
    vin = ""
    if pathname.startswith('/update_vehicle'):
        vin = pathname.split('/')[-1]

    if not value or (add_vehicle.VIN_not_exist(value, vin) and value.isalnum()):
        input_vehicle_values['VIN'] = value
    elif not value.isalnum():
        return 'VIN must be alphanumeric'
    else:
        return 'The VIN already exists.'

@app.callback(
    Output('model-name-placeholder', 'children'),
    Input('model-name', 'value')
)
def input_model_name(value):
    input_vehicle_values['model_name'] = value

@app.callback(
    Output('model-year-placeholder', 'children'),
    Input('model-year', 'value')
)
def input_model_year(value):
    input_vehicle_values['model_year'] = value

@app.callback(
    Output('manufacturer-placeholder', 'children'),
    Input('manufacturer', 'value')
)
def input_manufacturer(value):
    input_vehicle_values['manufacturer'] = value

def dropdown_color(index):
    new_dropdown = dcc.Dropdown(
        id={
            'type': 'filter-dropdown',
            'index': index
        },
        options=[{'label': i, 'value': i} for i in colors],
        style={'width': '50%'},
        placeholder='Select a color',

    )
    return new_dropdown

@app.callback(
    Output('dropdown-container', 'children'),
    [Input('add-color', 'n_clicks'),
     Input('delete-color', 'n_clicks')],
    State('dropdown-container', 'children'))
def display_colors(add_clicks, delete_clicks, children):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks yet'
        new_dropdown = dropdown_color(0)
        children.append(new_dropdown)
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    dif = ctx.inputs['add-color.n_clicks'] - ctx.inputs['delete-color.n_clicks']
    num_row = dif if dif > 0 else 0
    if button_id == 'add-color':
        new_dropdown = dropdown_color(num_row)
        children.append(new_dropdown)
    elif button_id == 'delete-color':
        if len(children) > 1:
            children.pop()
    return children

@app.callback(
    Output('color-error', 'children'),
    Input({'type': 'filter-dropdown', 'index': ALL}, 'value')
)
def display_output(values):
    select_colors['colors'] = []
    for value in values:
        if value is not None:
            if value in select_colors['colors']:
                return 'Duplicate colors are not allowed.'
            else:
                select_colors['colors'].append(value)

@app.callback(
    Output('invoice-price-error', 'children'),
    Input('invoice-price', 'value')
)
def input_invoice_price(value):
    if not value or add_vehicle.check_invoice_price(str(value)):
        input_vehicle_values['invoice_price'] = value
    else:
        return 'Invalid invoice price.'

@app.callback(
    Output('description-placeholder', 'children'),
    Input('description', 'value')
)
def input_invoice_price(value):
    input_vehicle_values['description'] = value

vehicle_type_details = {
    'Car': html.Div(id='Car', children=[
        html.Br(),
        html.Div(["Number of doors: ",
                  dcc.Input(id='num-of-doors',
                            placeholder="Input the number of doors",
                            style={'width': '20%'},
                            value=""
                            ),
                  html.Div(id='num-of-doors-error', style={'color': 'red'})]),
        html.Br()
    ]),
    'Convertible': html.Div(id='Convertible', children=[
        html.Br(),
        html.Div(["Roof type: ",
                  dcc.Input(id='roof-type',
                            placeholder="Input the roof type",
                            style={'width': '20%'},
                            value=""),
                  html.Div(id='roof-type-placeholder', style={'display': 'none'})]),
        html.Br(),
        html.Div(["Back seat count: ",
                  dcc.Input(id='back-seat-count',
                            placeholder="Input back seat count",
                            style={'width': '20%'},
                            value=""),
                  html.Div(id='back-seat-count-error', style={'color': 'red'})]),
        html.Br()
    ]),
    'SUV': html.Div(id='SUV', children=[
        html.Br(),
        html.Div(["Drivetrain type: ",
                  dcc.Input(id='drivetrain-type',
                            placeholder="Input drivetrain type",
                            style={'width': '20%'}),
                  html.Div(id='drivetrain-type-placeholder', style={'display': 'none'})]),
        html.Br(),
        html.Div(["Number of cupholders: ",
                  dcc.Input(id='num-of-cupholders',
                            placeholder="Input the number of cupholders",
                            style={'width': '20%'},
                            value=""),
                  html.Div(id='num-of-cupholders-error', style={'color': 'red'})]),
        html.Br()
    ]),
    'VanMinivan': html.Div(id='VanMinivan', children=[
        html.Br(),
        html.Div(["Has Driver’s Side Back Door: ",
                  dcc.Dropdown(
                      id='has-back-door',
                      options=[{'label': 'yes', 'value': '1'}, {'label': 'no', 'value': '0'}],
                      clearable=False,
                      placeholder='Select vehicle type',
                      style={'width': '50%'},
                      value=""),
                  html.Div(id='has-back-door-placeholder', style={'display': 'none'})]),
        html.Br()
    ]),
    'Truck': html.Div(id='Truck', children=[
        html.Br(),
        html.Div(["Cargo capacity: ",
                  dcc.Input(id='cargo-capacity',
                            placeholder="Input Cargo capacity (in tons)",
                            style={'width': '20%'},
                            value=""),
                  html.Div(id='cargo-capacity-error', style={'color': 'red'})]),
        html.Br(),
        html.Div(["Number of rear axles: ",
                  dcc.Input(id='num-of-rear-axles',
                            placeholder="Input the number of rear axles",
                            style={'width': '20%'},
                            value=""),
                  html.Div(id='num-of-rear-axles-error', style={'color': 'red'})]),
        html.Br(),
        html.Div(["Cargo cover type: ",
                  dcc.Input(id='cargo-cover-type',
                            placeholder="optional",
                            style={'width': '20%'},
                            value=""),
                  html.Div(id='cargo-cover-type-placeholder', style={'display': 'none'})]),
        html.Br()
    ]),
}

# For inventory clerk to get and check uname and password
def get_uname_pass_from_path(pathname):
    [uname, passw] = ["", ""]
    p = pathname.split('/')
    n = len(p)
    if n > 2:
        uname = p[n - 2]
        passw = p[n - 1]
        query = "SELECT Username, Password FROM User GROUP BY Username"
        df = pd.read_sql(query, mydb)
        li = df.to_dict('records')
        newli = {row["Username"]: row["Password"] for row in li}
        if newli[uname] != passw: [uname, passw] = ["", ""]
    return [uname, passw]

@app.callback(
    Output('type-placeholder', 'children'),
    Input('vehicle_type', 'value')
)
def input_vehicle_type(value):
    input_vehicle_values['vehicle_type'] = value

# input Car values
@app.callback(
    Output('num-of-doors-error', 'children'),
    Input('num-of-doors', 'value')
)
def input_car_num_of_doors(value):
    if value:
        try:
            int(value)
        except ValueError:
            return 'Invalid number.'
    input_type_values['Car']['num_of_doors'] = value

# input Convertible values
@app.callback(
    Output('roof-type-placeholder', 'children'),
    Input('roof-type', 'value')
)
def input_convertible_roof_type(value):
    input_type_values['Convertible']['roof_type'] = value

@app.callback(
    Output('back-seat-count-error', 'children'),
    Input('back-seat-count', 'value')
)
def input_convertible_back_seat_count(value):
    if value:
        try:
            int(value)
        except ValueError:
            return 'Invalid number.'
    input_type_values['Convertible']['back_seat_count'] = value

# input SUV values
@app.callback(
    Output('drivetrain-type-placeholder', 'children'),
    Input('drivetrain-type', 'value')
)
def input_SUV_drivetrain_type(value):
    input_type_values['SUV']['drivetrain_type'] = value

@app.callback(
    Output('num-of-cupholders-error', 'children'),
    Input('num-of-cupholders', 'value')
)
def input_SUV_num_of_cupholders(value):
    if value:
        try:
            int(value)
        except ValueError:
            return 'Invalid number.'
    input_type_values['SUV']['num_of_cupholders'] = value

# input VanMinivan values
@app.callback(
    Output('has-back-door-placeholder', 'children'),
    Input('has-back-door', 'value')
)
def input_VanMinivan_has_back_door(value):
    input_type_values['VanMinivan']['has_back_door'] = value

# input Truck values
@app.callback(
    Output('cargo-capacity-error', 'children'),
    Input('cargo-capacity', 'value')
)
def input_truck_cargo_capacity(value):
    if value:
        try:
            int(value)
        except ValueError:
            return 'Invalid number.'
    input_type_values['Truck']['num_of_rear_axles'] = value

@app.callback(
    Output('num-of-rear-axles-error', 'children'),
    Input('num-of-rear-axles', 'value')
)
def input_truck_num_of_rear_axles(value):
    if value:
        try:
            int(value)
        except ValueError:
            return 'Invalid number.'
    input_type_values['Truck']['cargo_capacity'] = value

@app.callback(
    Output('cargo-cover-type-placeholder', 'children'),
    Input('cargo-cover-type', 'value')
)
def input_truck_cargo_cover_type(value):
    input_type_values['Truck']['cargo_cover_type'] = value

@app.callback(
    [Output('errors', 'children'),
    ],
    Input('save', 'n_clicks'),
    [State('VIN-error', 'children'),
     State('invoice-price-error', 'children'),
     State('color-error', 'children'),
     State('url', 'pathname')
     ]
)
def saveVehicle(n_clicks, VIN_children, invoice_price_children, color_chilren, pathname):
    if n_clicks == 0: return ["",]
    if VIN_children or invoice_price_children or color_chilren:
        # or type_children1 or type_children2 or type_children3 or type_children4 or type_children5 or type_children6:
        return ["Error, can't saved.",]
    if not select_colors:
        return ["Any fields except Description can't be empty. Otherwise can't saved."]
    for k, val in input_vehicle_values.items():
        if k != 'description' and val == "":
            return ["Any fields except Description can't be empty. Otherwise can't saved."]
    try:
        add_vehicle.save_vehicle(list(input_vehicle_values.values())),
        for color in select_colors['colors']:
            add_vehicle.save_colors([input_vehicle_values['VIN'], color])
    except:
        return ["Error, can't saved."]
    [uname, passw] = get_uname_pass_from_path(pathname)
    return [dcc.Location(href='/add_type_details/%s/%s' % (uname, passw), id='to_add_vehicle_page')]

@app.callback([Output('details_errors', 'children'),
               ],
              Input('save-vehicle-type-details', 'n_clicks'),
              State('url', 'pathname'))
def saveVehicleTypeDetails(save, pathname):
    vehicle_type = input_vehicle_values['vehicle_type']
    vehicle_type_values = input_type_values[vehicle_type].values()
    if save == 0: return [""]
    if vehicle_type != "Truck":
        for val in vehicle_type_values:
            if not val:
                return ["Any fields (except 'Cargo cover type' for Truck) can't be empty. Otherwise can't saved."]
    else:
        for k, val in input_type_values[vehicle_type].items():
            if not val and k != 'cargo_cover_type':
                return ["Any fields (except 'Cargo cover type' for Truck) can't be empty. Otherwise can't saved."]
    try:
        add_vehicle.call_save_type_method(vehicle_type, [input_vehicle_values['VIN']] + list(vehicle_type_values)),
    except:
        return ["Error, can't saved."]
    [uname, passw] = get_uname_pass_from_path(pathname)
    return [dcc.Location(href='/inventory_clerk/show_details/%s/%s/%s' % (input_vehicle_values['VIN'], uname, passw), id='to_add_vehicle_page')]


def check_VIN(vin):
    get_vin = add_vehicle.get_VIN(vin)
    return get_vin
# inventory clerk end


#View report start

# sc1_sql = "SELECT vc.Color, COUNT(v.VIN) AS Count FROM Vehicle AS v INNER JOIN VehicleColor AS vc ON v.VIN=vc.VIN WHERE v.Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 30 DAY) AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY vc.Color ORDER BY vc.Color;"
# sc2_sql = "SELECT vc.Color, COUNT(v.VIN) AS Count FROM Vehicle AS v INNER JOIN VehicleColor AS vc ON v.VIN=vc.VIN WHERE v.Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 1 YEAR) AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY vc.Color ORDER BY vc.Color;"
# sc3_sql = "SELECT vc.Color, COUNT(v.VIN) AS Count FROM Vehicle AS v INNER JOIN VehicleColor AS vc ON v.VIN=vc.VIN WHERE v.Sold_date IS NOT NULL GROUP BY vc.Color ORDER BY vc.Color;"

sc_sql="SELECT DISTINCT(vc0.Color),\
        COALESCE(NULLIF(A.Count,''),'0') AS '30 Days Sales', \
        COALESCE(NULLIF(B.Count,''),'0') AS '1 Year Sales', \
        COALESCE(NULLIF(C.Count,''),'0') AS 'All Time Sales'\
        FROM (SELECT DISTINCT(vc.Color) AS Color FROM VehicleColor AS vc UNION SELECT 'Multiple' FROM VehicleColor AS vc) AS vc0\
        LEFT JOIN\
        (SELECT vc.Color AS Color, COUNT(vc1.VIN) AS Count FROM (SELECT VIN, COUNT(Color) FROM VehicleColor GROUP BY VIN HAVING COUNT(Color)=1) AS vc1\
        INNER JOIN VehicleColor AS vc\
        ON vc1.VIN=vc.VIN\
        INNER JOIN Vehicle AS v\
        ON vc1.VIN=v.VIN\
        WHERE v.Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 29 DAY) AND (SELECT MAX(Sold_date) FROM Vehicle)\
        GROUP BY vc.Color\
        UNION\
        SELECT 'Multiple' AS Color, COUNT(vc2.All_Time_Sales) AS Count FROM (SELECT VIN, COUNT(Color) AS All_Time_Sales FROM VehicleColor GROUP BY VIN HAVING COUNT(Color)!=1) AS vc2\
        INNER JOIN Vehicle AS v\
        ON vc2.VIN=v.VIN\
        WHERE v.Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 29 DAY) AND (SELECT MAX(Sold_date) FROM Vehicle)) AS A\
        ON A.Color=vc0.Color\
        LEFT JOIN \
        (SELECT  vc.Color AS Color, COUNT(vc1.VIN) AS Count FROM (SELECT VIN, COUNT(Color) FROM VehicleColor GROUP BY VIN HAVING COUNT(Color)=1) AS vc1\
        INNER JOIN VehicleColor AS vc\
        ON vc1.VIN=vc.VIN\
        INNER JOIN Vehicle AS v\
        ON vc1.VIN=v.VIN\
        WHERE v.Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 1 YEAR)+1 AND (SELECT MAX(Sold_date) FROM Vehicle)\
        GROUP BY vc.Color\
        UNION\
        SELECT 'Multiple' AS Color, COUNT(vc2.All_Time_Sales) AS Count FROM (SELECT VIN, COUNT(Color) AS All_Time_Sales FROM VehicleColor GROUP BY VIN HAVING COUNT(Color)!=1) AS vc2\
        INNER JOIN Vehicle AS v\
        ON vc2.VIN=v.VIN\
        WHERE v.Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 1 YEAR)+1 AND (SELECT MAX(Sold_date) FROM Vehicle)) AS B\
        ON B.Color=vc0.Color\
        LEFT JOIN\
        (SELECT  vc.Color AS Color, COUNT(vc1.VIN) AS Count FROM (SELECT VIN, COUNT(Color) FROM VehicleColor GROUP BY VIN HAVING COUNT(Color)=1) AS vc1\
        INNER JOIN VehicleColor AS vc\
        ON vc1.VIN=vc.VIN\
        INNER JOIN Vehicle AS v\
        ON vc1.VIN=v.VIN\
        WHERE Sold_date IS NOT NULL\
        GROUP BY vc.Color\
        UNION\
        SELECT 'Multiple' AS Color, COUNT(vc2.All_Time_Sales) AS Count FROM (SELECT VIN, COUNT(Color) AS All_Time_Sales FROM VehicleColor GROUP BY VIN HAVING COUNT(Color)!=1) AS vc2\
        INNER JOIN Vehicle AS v\
        ON vc2.VIN=v.VIN\
        WHERE Sold_date IS NOT NULL) AS C\
        ON C.Color=vc0.Color\
        ORDER BY vc0.Color;"



st_sql="SELECT DISTINCT(Vehicle.Type), COALESCE(NULLIF(A.Count,''),'0') AS '30 Days Sales', COALESCE(NULLIF(B.Count,''),'0') AS '1 Year Sales', COALESCE(NULLIF(C.Count,''),'0') AS 'All Time Sales' FROM Vehicle\
        LEFT JOIN \
        (SELECT Type, COUNT(VIN) AS Count FROM Vehicle WHERE Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 29 DAY) AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY Type) AS A ON Vehicle.Type=A.Type\
        LEFT JOIN \
        (SELECT Type, COUNT(VIN) AS Count FROM Vehicle WHERE Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 1 YEAR)+1 AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY Type) AS B ON Vehicle.Type=B.Type\
        LEFT JOIN\
        (SELECT Type, COUNT(VIN) AS Count FROM Vehicle WHERE Sold_date IS NOT NULL GROUP BY Type) AS C ON Vehicle.Type=C.Type\
        ORDER BY Vehicle.Type;"


# st1_sql = "SELECT Type, COUNT(VIN) AS Count FROM Vehicle WHERE Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 30 DAY) AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY Type ORDER BY Type;"
# st2_sql = "SELECT Type, COUNT(VIN) AS Count FROM Vehicle WHERE Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 1 YEAR) AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY Type ORDER BY Type;"
# st3_sql = "SELECT Type, COUNT(VIN) AS Count FROM Vehicle WHERE Sold_date IS NOT NULL GROUP BY Type ORDER BY Type;"

# sm1_sql = "SELECT Manufacturer_name, COUNT(VIN) FROM Vehicle WHERE Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 30 DAY) AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY Manufacturer_name ORDER BY Manufacturer_name;"
# sm2_sql = "SELECT Manufacturer_name, COUNT(VIN) FROM Vehicle WHERE Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 1 YEAR) AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY Manufacturer_name ORDER BY Manufacturer_name;"
# sm3_sql = "SELECT Manufacturer_name, COUNT(VIN) FROM Vehicle WHERE Sold_date IS NOT NULL GROUP BY Manufacturer_name ORDER BY Manufacturer_name;"


sm_sql="SELECT DISTINCT(v.Manufacturer_name), COALESCE(NULLIF(A.Count,''),'0') AS '30 Days Sales', COALESCE(NULLIF(B.Count,''),'0') AS '1 Year Sales', COALESCE(NULLIF(C.Count,''),'0') AS 'All Time Sales' FROM (SELECT Manufacturer_name FROM Vehicle WHERE Sold_date IS NOT NULL) AS v\
        LEFT JOIN \
        (SELECT Manufacturer_name, COUNT(VIN) AS Count FROM Vehicle WHERE Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 29 DAY) AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY Manufacturer_name) AS A ON v.Manufacturer_name=A.Manufacturer_name\
        LEFT JOIN \
        (SELECT Manufacturer_name, COUNT(VIN) AS Count FROM Vehicle WHERE Sold_date BETWEEN DATE_SUB((SELECT MAX(Sold_date) FROM Vehicle), INTERVAL 1 YEAR)+1 AND (SELECT MAX(Sold_date) FROM Vehicle) GROUP BY Manufacturer_name) AS B ON v.Manufacturer_name=B.Manufacturer_name\
        LEFT JOIN\
        (SELECT Manufacturer_name, COUNT(VIN) AS Count FROM Vehicle WHERE Sold_date IS NOT NULL GROUP BY Manufacturer_name) AS C ON v.Manufacturer_name=C.Manufacturer_name\
        ORDER BY Manufacturer_name;"



bcs_sql = "SELECT cc.Customer_Name, v.Sold_price, v.Invoice_price, CONCAT(ROUND(v.Sold_price*100/v.Invoice_price,2),'%') AS Ratio, CONCAT(u.Fname, ' ',u.Lname) AS 'Sales Person', v.VIN, v.Sold_date FROM (SELECT CONCAT(ip.Fname, '/', ip.Lname) AS Customer_Name, ip.CustomerID FROM IndividualPerson AS ip UNION ALL SELECT b.Business_name AS Customer_Name, b.CustomerID FROM Business AS b) AS cc INNER JOIN Vehicle AS v ON cc.CustomerID= v.CustomerID INNER JOIN User AS u ON v.Sold_by = u.Username WHERE v.Sold_price/v.Invoice_price < 1.0 ORDER BY v.Sold_date DESC, v.Sold_price/v.Invoice_price DESC;"


atii_sql = "SELECT DISTINCT(Vehicle.Type), COALESCE(NULLIF(A.Average_Time_in_Inventory,''),'N/A') AS 'Average Time in Inventory'\
             FROM Vehicle\
             LEFT JOIN (SELECT Type, ROUND(AVG(DATEDIFF(Sold_date,Add_date)),2) AS Average_Time_in_Inventory FROM Vehicle WHERE Sold_date IS NOT NULL GROUP BY Type) AS A\
             ON Vehicle.Type=A.Type\
             ORDER BY Vehicle.Type;"
ps_sql = "SELECT Vendor_name, SUM(Quantity), SUM(Part_price*Quantity) AS TotalSpent FROM Part GROUP BY Vendor_name ORDER BY TotalSpent DESC;"

# The fourth report: Gross Customer Income
# Part1: a listing of the top 15 customers
gci_sql = 'WITH cte_customer AS ( \
                SELECT CONCAT(ip.Fname, " ", ip.Lname) AS n, ip.CustomerID, ip.ID AS ID FROM IndividualPerson AS ip \
                    UNION ALL \
                SELECT b.Business_name AS n, b.CustomerID, b.Tax_ID AS ID FROM Business AS b) \
            SELECT ot.ID AS "ID/TaxID", ot.n AS Customer_name, ot.fsd AS First_Consumption_Date, ot.lsd AS Laset_Consumption_Date, ot.VIN AS Num_of_Sales, ot.repair_times AS Num_of_Repair, (IFNULL(sp.Sold_price, 0)+IFNULL(lf.Labor_fee, 0)+IFNULL(pp.Part_price, 0)) AS Gross_Income \
            FROM (SELECT cc.ID, cc.n, LEAST(IFNULL(MIN(r.Start_date),MIN(v.Sold_date)), MIN(v.Sold_date)) AS fsd, GREATEST(IFNULL(MAX(r.Start_date), MAX(v.Sold_date)), MAX(v.Sold_date)) AS lsd, COUNT(DISTINCT v.VIN) AS VIN, COUNT(DISTINCT CONCAT(r.VIN, r.CustomerID, r.Start_date)) AS repair_times, cc.CustomerID FROM cte_customer AS cc \
                LEFT JOIN Vehicle AS v ON cc.CustomerID= v.CustomerID \
                LEFT JOIN Repair AS r ON cc.CustomerID = r.CustomerID \
                LEFT JOIN Part AS p ON cc.CustomerID = p.CustomerID \
                GROUP BY cc.CustomerID, cc.n, cc.ID) AS ot \
            LEFT JOIN (SELECT cc.CustomerID,SUM(v.Sold_price) AS Sold_price FROM cte_customer AS cc \
                INNER JOIN Vehicle AS v ON cc.CustomerID= v.CustomerID \
                GROUP BY cc.CustomerID) AS sp ON sp.CustomerID = ot.CustomerID \
            LEFT JOIN (SELECT cc.CustomerID, SUM(r.Labor_fee) AS Labor_fee FROM cte_customer AS cc \
                INNER JOIN Repair AS r ON cc.CustomerID = r.CustomerID \
                GROUP BY cc.CustomerID) AS lf ON lf.CustomerID = ot.CustomerID \
            LEFT JOIN (SELECT cc.CustomerID, cc.n, SUM(p.Part_price*p.Quantity) AS Part_price FROM cte_customer AS cc \
                INNER JOIN Part AS p ON cc.CustomerID = p.CustomerID \
                GROUP BY cc.CustomerID, cc.n) AS pp ON pp.CustomerID = ot.CustomerID \
            ORDER BY Gross_Income DESC, Laset_Consumption_Date DESC LIMIT 15;'


# Part2: 2.1 a section for vehicle
def get_gci_vehicle_sql(customerID):
    gci_vehicle_sql = 'SELECT v.Sold_date, v.Sold_price, v.VIN, v.Model_year, v.Manufacturer_name, v.Model_name, CONCAT(u.Fname, " ", u.Lname) AS Sold_by FROM Vehicle AS v \
                                INNER JOIN User AS u ON u.Username=v.Sold_by \
                                WHERE v.CustomerID=%s \
                                ORDER by v.Sold_date DESC, v.VIN ASC;' % customerID
    return gci_vehicle_sql


# Part2: 2.2 a section for repairs
def get_gci_repairs_sql(customerID):
    gci_repairs_sql = 'SELECT r.Start_date, r.Complete_date, r.VIN, r.Odometer, IFNULL(p.Part_costs, 0) AS Part_costs, r.Labor_fee AS Labor_costs, IFNULL(p.Part_costs, 0)+r.Labor_fee AS Total_costs, CONCAT(u.Fname, " ", u.Lname) AS Service_writer \
                                FROM Repair AS r \
                                LEFT JOIN (SELECT SUM(p.Part_price*p.Quantity) AS Part_costs, p.CustomerID, p.Start_date, p.VIN FROM Part AS p \
                                    INNER JOIN Repair AS r ON p.CustomerID = r.CustomerID AND p.Start_date = r.Start_date AND p.VIN = r.VIN \
                                    GROUP by p.CustomerID, p.Start_date, p.VIN) AS p ON p.CustomerID = r.CustomerID AND p.Start_date = r.Start_date AND p.VIN = r.VIN \
                                INNER JOIN User AS u ON r.Username=u.Username \
                                WHERE r.CustomerID=%s \
                                ORDER BY r.Start_date DESC, r.Complete_date IS NULL DESC, r.Complete_date DESC, r.VIN;' % customerID
    return gci_repairs_sql


# Fifth report: Repairs by Manufacturer/Type/Model
# Part1: list for each manufacturer
rbmtm_list_sql = 'SELECT m.Manufacturer_name, COUNT(CONCAT(r.VIN, r.Start_date, r.CustomerID)) AS Repair_count, SUM(IFNULL(p.Part_price,0)) AS Part_costs, SUM(IFNULL(r.Labor_fee,0)) AS Labor_costs, SUM(IFNULL(r.Labor_fee,0) + IFNULL(p.Part_price,0)) AS Total_costs \
                            FROM Repair AS r \
                            INNER JOIN Vehicle AS v ON r.VIN = v.VIN \
                            RIGHT JOIN Manufacturer AS m ON m.Manufacturer_name = v.Manufacturer_name \
                            LEFT JOIN (SELECT SUM(p.Part_price*p.Quantity) AS Part_price, p.CustomerID, p.Start_date, p.VIN FROM Part AS p \
                                INNER JOIN Repair AS r ON p.CustomerID = r.CustomerID AND p.Start_date = r.Start_date AND p.VIN = r.VIN \
                                GROUP by p.CustomerID, p.Start_date, p.VIN) AS p ON (r.VIN=p.VIN AND r.CustomerID=p.CustomerID AND r.Start_date=p.Start_date) \
                            GROUP BY m.Manufacturer_name \
                            ORDER BY m.Manufacturer_name;'


# Part2: drill-down for manufacturers and further details for each model
def get_rbmtm_drill_sql(manufacturer_name):
    rbmtm_drill_sql = 'WITH cte_type_repair AS (SELECT v.Type, COUNT(CONCAT(r.VIN, r.Start_date, r.CustomerID)) AS Repair_count, SUM(p.Part_price) AS Part_costs, SUM(r.Labor_fee) AS Labor_costs, SUM(IFNULL(r.Labor_fee,0) + IFNULL(p.Part_price,0)) AS Total_costs FROM Repair AS r \
                                                LEFT JOIN (SELECT SUM(p.Part_price*p.Quantity) AS Part_price, p.CustomerID, p.Start_date, p.VIN FROM Part AS p \
                                                            INNER JOIN Repair AS r ON p.CustomerID = r.CustomerID AND p.Start_date = r.Start_date AND p.VIN = r.VIN \
                                                            GROUP by p.CustomerID, p.Start_date, p.VIN) AS p ON r.VIN=p.VIN AND r.CustomerID=p.CustomerID AND r.Start_date=p.Start_date \
                                                            INNER JOIN Vehicle AS v ON r.VIN = v.VIN \
                                                WHERE v.Manufacturer_name="%s" \
                                                GROUP BY v.Type), \
                            cte_model_repair AS (SELECT v.Type, CONCAT(" ", v.Model_name) AS Model_name, COUNT(CONCAT(r.VIN, r.Start_date, r.CustomerID)) AS Repair_count, SUM(p.Part_price) AS Part_costs, SUM(r.Labor_fee) AS Labor_costs, SUM(IFNULL(r.Labor_fee,0) + IFNULL(p.Part_price,0)) AS Total_costs FROM Repair AS r \
                                                LEFT JOIN (SELECT SUM(p.Part_price*p.Quantity) AS Part_price, p.CustomerID, p.Start_date, p.VIN FROM Part AS p \
                                                            INNER JOIN Repair AS r ON p.CustomerID = r.CustomerID AND p.Start_date = r.Start_date AND p.VIN = r.VIN \
                                                            GROUP by p.CustomerID, p.Start_date, p.VIN) AS p ON r.VIN=p.VIN AND r.CustomerID=p.CustomerID AND r.Start_date=p.Start_date \
                                                            INNER JOIN Vehicle AS v ON r.VIN = v.VIN \
                                                WHERE v.Manufacturer_name="%s" \
                                                GROUP BY v.Type, v.Model_name) \
                        SELECT tmo.Type_Model, tmo.Repair_count, tmo.Part_costs, tmo.Labor_costs, tmo.Total_costs \
                        FROM ((SELECT ctr.Type, ctr.Type AS Type_Model, ctr.Repair_count AS Repair_count_type, ctr.Repair_count, ctr.Part_costs, ctr.Labor_costs, ctr.total_costs FROM cte_type_repair AS ctr) \
                                    UNION ALL \
                            (SELECT cmr.Type, cmr.Model_name AS Type_Model, ctr.Repair_count AS Repair_count_type, cmr.Repair_count, cmr.Part_costs, cmr.Labor_costs, cmr.total_costs FROM cte_model_repair AS cmr \
                                INNER JOIN cte_type_repair AS ctr ON ctr.Type = cmr.Type)) AS tmo \
                        ORDER BY tmo.Repair_count_type DESC, tmo.Type, tmo.Repair_count DESC;' % (manufacturer_name, manufacturer_name)
    return rbmtm_drill_sql


def get_customer_ID_sql(ID):
    customer_id_sql = 'SELECT cc.CustomerID FROM \
                                    (SELECT CONCAT(ip.Fname, " ", ip.Lname) AS n, ip.CustomerID, ip.ID AS ID FROM IndividualPerson AS ip \
                                        UNION ALL \
                                    SELECT b.Business_name AS n, b.CustomerID, b.Tax_ID AS ID FROM Business AS b) AS cc \
                                 WHERE cc.ID="%s"' % ID
    return customer_id_sql


ms_sql = "SELECT CONCAT(CONVERT(YEAR(Sold_date), CHAR), '/', CONVERT(MONTH(Sold_date), CHAR)) AS Year_and_Month, COUNT(VIN) AS 'Num of Sold Vehicles', SUM(Sold_price) AS 'Total Sales Income', SUM(Sold_price-Invoice_price) AS 'Total Net Income', CONCAT(ROUND(SUM(Sold_price)*100/SUM(Invoice_price),2),'%') AS Ratio FROM Vehicle WHERE Sold_date IS NOT NULL GROUP BY YEAR(Sold_date), MONTH(Sold_date), Year_and_Month ORDER BY YEAR(Sold_date) DESC, MONTH(Sold_date) DESC;"


# Ninth report: part 2: drill_down report for each year/month result
def get_ms_res_sql(year, month):
    ms_res_sql = "SELECT CONCAT(u.Fname, ' ', u.Lname) AS Name, COUNT(v.VIN) AS VIN_Count, SUM(v.Sold_price) AS Sold_price FROM Vehicle AS v INNER JOIN User AS u ON v.Sold_by=u.Username WHERE MONTH(Sold_date)= %s AND YEAR(Sold_date)=%s GROUP BY u.Username ORDER BY COUNT(v.VIN) DESC, SUM(v.Sold_price) DESC;" % (month, year)
    return ms_res_sql


def get_salesbycolor(username):
    df_sc = pd.read_sql(sc_sql, mydb)
    salesbycolor=html.Div([
        html.H1("Sales by Color", style={'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="sbc_to_report_menu", href="/logged_in_manager/" + username, refresh=True),
        html.Table(children=[
                    dbc.Container([
                        #dbc.Label('Sales by Color in the previous 30 days'),
                        html.Br(),
                        dash_table.DataTable(
                            id='table_sc',
                            columns=[{"name": i, "id": i} for i in df_sc.columns],
                            data=df_sc.to_dict('records'),

                        )
                        ]),
 
    ])
    ])
    return salesbycolor


def get_salesbytype(username):
    df_st = pd.read_sql(st_sql, mydb)
    salesbytype=html.Div([
        html.H1("Sales by Type", style = {'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="sbt_to_report_menu", href="/logged_in_manager/" + username, refresh=True),
        html.Table(children=[
                    dbc.Container([
                        #dbc.Label('Sales by Type in the previous 30 days'),
                        html.Br(),
                        dash_table.DataTable(
                            id='table_st',
                            columns=[{"name": i, "id": i} for i in df_st.columns],
                            data=df_st.to_dict('records'),
                        )
                        ]),                     
                        ])
    ])
    return salesbytype


def get_salesbymanufacturer(username):
    df_sm = pd.read_sql(sm_sql, mydb)

    salesbymanufacturer=html.Div([
        html.H1("Sales by Manufacturer", style = {'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="sbm_to_report_menu", href="/logged_in_manager/" + username, refresh=True),
        html.Table(children=[
                    dbc.Container([
                        #dbc.Label('Sales by Manufacturer in the previous 30 days'),
                        html.Br(),
                        dash_table.DataTable(
                            id='table_sm',
                            columns=[{"name": i, "id": i} for i in df_sm.columns],
                            data=df_sm.to_dict('records'),
                        )
                        ]),

                        
                        ])
    ])
  
    return salesbymanufacturer


def get_belowcostsales(username):
    df_bcs = pd.read_sql(bcs_sql, mydb)
    belowcostsales=html.Div([
        html.H1("Below Cost Sales", style = {'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="bcs_to_report_menu", href="/logged_in_manager/" + username, refresh=True),
        # html.Table(children=[
        #           dbc.Container([
        #               dbc.Label('monthly sales'),
        #               html.Br(),
                        dash_table.DataTable(
                          # id='table_ms1',
                            columns=[{"name": i, "id": i} for i in df_bcs.columns],
                            data=df_bcs.to_dict('records'),

                            style_data_conditional=[
                                {
                                    'if': {

                                        'filter_query': '{Ratio} <=95%'
                                    },
                                    'background-color': 'red'
                                },

                            ],
                        )
                        
                        ])
    return belowcostsales


def get_averagetimeininventory(username):
    df_atii = pd.read_sql(atii_sql, mydb)
    averagetimeininventory=html.Div([
        html.H1("Average Time in Inventory", style = {'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="atii_to_report_menu", href="/logged_in_manager/" + username, refresh=True),
        html.Table(children=[
                    dbc.Container([
                        #dbc.Label('Average Time in Inventory'),
                        html.Br(),
                        dash_table.DataTable(
                            id='table_atii',
                            columns=[{"name": i, "id": i} for i in df_atii.columns],
                            data=df_atii.to_dict('records'),
                        )
                        ])
                        ])
    ])
    return averagetimeininventory


def get_partsstatistics(username):
    df_ps = pd.read_sql(ps_sql, mydb)
    partsstatistics=html.Div([
        html.H1("Parts Statistics", style = {'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="ps_to_report_menu", href="/logged_in_manager/" + username, refresh=True),
        html.Table(children=[
                    dbc.Container([
                        #dbc.Label('Parts Statistics'),
                        html.Br(),
                        dash_table.DataTable(
                            id='table_ps',
                            columns=[{"name": i, "id": i} for i in df_ps.columns],
                            data=df_ps.to_dict('records'),
                        )
                        ])
                        ])
    ])
    return partsstatistics


# Ninth report: Monthly Sales
# Part 1: a summary page
def get_monthly_sales(username):
    df_ms=pd.read_sql(ms_sql, mydb)
    data = df_ms.to_dict('records')
    df = pd.DataFrame(data)
    # df_ms['Year_Month_Result'] = "[Link](/view_report_monthly_result/%s/" % username + df_ms["Year_Month_Result"] + ")"
    monthlysales=html.Div([
        html.H1("Monthly Sales", style = {'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="ms_to_report_menu", href="/logged_in_manager/" + username, refresh=True),
        generate_table(df, '/view_report_monthly_result/%s' % username, 'Year_and_Month')
        # html.Table(children=[
        #           dbc.Container([
        #               dbc.Label('monthly sales'),
        #               html.Br(),
        #                 dash_table.DataTable(
        #                     id='table_ms1',
        #                     columns=[{"name": "Year/Month result", "id": "Year_Month_Result", "type": "text", "presentation": "markdown"}, {"name": "Year", "id": "Year"}, {"name": "Month", "id": "Month"}, {"name": "Total Number of Vehicles Sold", "id": "Total Number of Vehicles Sold"}, {"name": "Total Sales Income", "id":"Total Sales Income"}, {"name": "Ratio", "id":"Ratio"}],
        #                     data=df_ms.to_dict('results'),
        #                     filter_action="native",
        #                     sort_action="native",
        #                     sort_mode="multi",
        #                     column_selectable="single",
        #                     style_data_conditional=[
        #                         {
        #                             'if': {
        #                                 'filter_query': '{Ratio} >=1.25'
        #                             },
        #                             'background-color': 'green'
        #                         },
        #                         {
        #                             'if': {
        #                                 'filter_query': '{Ratio} <=1.1'
        #                             },
        #                             'background-color':'yellow'
        #                         },
        #                     ],
        #                 )
        #                 ])
        #               ])
    ])
    return monthlysales


# Part 2: drill_down report for each year/month result
def get_monthly_sales_result(year, month, username):
    df_ms_res = pd.read_sql(get_ms_res_sql(int(year), int(month)), mydb)
    data = df_ms_res.to_dict('records')
    data[0]['Name'] = '🏆' + data[0]['Name']
    monthlysales_result = html.Div([
        html.H1("%s/%s Monthly Sales drill-down Result" % (year, month), style={'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="drill-down-to-ms", href="/view_report_MS/" + username, refresh=True),
        html.Br(), html.Br(), html.Div(id='top-sales-person'),
        html.Table(children=[
            dbc.Container([
                html.Br(),
                dash_table.DataTable(
                    id='monthly_sales_result_table',
                    columns=[{"name": i, "id": i} for i in df_ms_res.columns],
                    data=data,
                )
            ]),
        ]),
    ])
    return monthlysales_result


@app.callback(Output('top-sales-person', 'children'),
    Input('monthly_sales_result_table', 'data'))
def display_top_sales_person(data):
    return data[0]['Name'].replace('🏆', '') + " is the top sales person for the month"


def generate_table(dataframe, url, key):
    return html.Table(
        # Header
        [html.Tr([html.Th('Year/Month' if col == 'Year_and_Month' else col,
                          style={'border': '1px solid LightGrey', 'backgroundColor': 'WhiteSmoke', 'padding': '9px'})
                  for col in dataframe.columns])] +
        # Body
        [html.Tr([
            html.Td(html.Div(dcc.Link(dataframe.iloc[i][col], href=url + '/%s' % dataframe.iloc[i][col], refresh=True)) if col == key else dataframe.iloc[i][col], style={'border': '1px solid LightGrey', 'padding': '9px'} ) for col in dataframe.columns
        ],  style={'backgroundColor': 'Green' if "Ratio" in dataframe.columns and float(dataframe.iloc[i][list(dataframe.columns).index("Ratio")].strip('%'))/100 >= 1.25 else ('Yellow' if 'Ratio' in dataframe.columns and float(dataframe.iloc[i][list(dataframe.columns).index("Ratio")].strip('%'))/100 <= 1.1 else 'White')}) for i in range(len(dataframe))],
            style={'border-collapse': 'collapse', 'width': '70%', 'font-size': '13px'}
    )


# The fourth report: Gross Customer Income
# Part 1.first part is a listing of the top 15 customers
def get_gross_customer_income(username):
    df_gci = pd.read_sql(gci_sql, mydb)
    data = df_gci.to_dict('records')
    df = pd.DataFrame(data)
    # df_gci = pd.read_sql(gci_sql, mydb)
    # df_gci["ID/TaxID"] = "[" + df_gci["ID/TaxID"] + "](/gci_detail/" + df_gci["ID/TaxID"] + ")"

    gross_customer_income = html.Div([
        html.H1("Gross Customer Income", style={'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="gci_to_report_menu", href="/logged_in_manager/" + username, refresh=True),
        html.Br(), html.Br(),
        html.Div("The top 15 customers:"),
        generate_table(df, '/gci_detail/%s' % username, 'ID/TaxID')
        # html.Table(children=[
        #     dbc.Container([
        #         html.Br(),
        #         dbc.Label('The top 15 customers:'),
        #         html.Br(),
        #         dash_table.DataTable(
        #             id='gross_income_table',
        #             # columns=[{"name": i, "id": i} for i in df_gci.columns],
        #             # data=df_gci.to_dict('records'),
        #             columns=[{"name": "ID/TaxID", "id": "ID/TaxID", "type": "text", "presentation": "markdown"},
        #                      {"name": "Customer_name", "id": "Customer_name"}, {"name": "First_Consumption_Date", "id": "First_Consumption_Date"},
        #                      {"name": "Laset_Consumption_Date", "id": "Laset_Consumption_Date"},
        #                      {"name": "Num_of_Vehicle", "id": "Num_of_Vehicle"}, {"name": "Num_of_Repair", "id": "Num_of_Repair"},
        #                      {"name": "Gross_Income", "id": "Gross_Income"}],
        #             css=[dict(selector='img[alt=Plotly]', rule='height: 50px;')],
        #             data=df_gci.to_dict('results'),
        #             filter_action="native",
        #             sort_action="native",
        #             sort_mode="multi",
        #             column_selectable="single",
        #
        #         )
        #     ]),
        # ]),
    ])
    return gross_customer_income


# The fourth report: Gross Customer Income
# Part 2. a drill-down for the selected customer: a section for vehicle sales and a section for repairs
def get_detail_of_gi(ID, username):
    df_customer_id = pd.read_sql(get_customer_ID_sql(ID), mydb)
    customerID = int(df_customer_id.to_dict()["CustomerID"][0])
    df_gci_vehicle = pd.read_sql(get_gci_vehicle_sql(customerID), mydb)
    df_gci_repairs = pd.read_sql(get_gci_repairs_sql(customerID), mydb)
    drill_down_of_gi = html.Div([
        html.H1("Gross Customer Income drill-down for the selected customer", style={'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="drill-down-to-gci", href="/view_report_GCI/" + username, refresh=True),

        html.Table(children=[
            dbc.Container([
                dbc.Label('Vehicle section:'),
                html.Br(),
                dash_table.DataTable(
                    id='gci_vehicle_table',
                    columns=[{"name": i, "id": i} for i in df_gci_vehicle.columns],
                    data=df_gci_vehicle.to_dict('records'),
                )
            ]),
            dbc.Container([
                dbc.Label('Repairs section:'),
                html.Br(),
                dash_table.DataTable(
                    id='gci_repairs_table',
                    columns=[{"name": i, "id": i} for i in df_gci_repairs.columns],
                    data=df_gci_repairs.to_dict('records'),
                )
            ]),
        ]),
    ])
    return drill_down_of_gi


# The fifth report:Repairs by Manufacturer/Type/Model
# 1.first part will list for each manufacturer
def get_repairs_by_MTM(username):
    df_rbmtm_list = pd.read_sql(rbmtm_list_sql, mydb)
    data = df_rbmtm_list
    df = pd.DataFrame(data)
    repairs_by_MTM = html.Div([

        html.H1("Repairs by Manufacturer/Type/Model", style = {'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="rbmtm_to_report_menu", href="/logged_in_manager/" + username, refresh=True),
        generate_table(df, '/drill_down/%s' % username, 'Manufacturer_name')
    ])
    return repairs_by_MTM


# The fifth report:Repairs by Manufacturer/Type/Model
# 2.drill-down for manufacturers
def get_repair_drill_down(manufacturer_name, username):
    df_rbmtm_drill = pd.read_sql(get_rbmtm_drill_sql(manufacturer_name), mydb)
    repairs_by_MTM_drill_down = html.Div([
        html.H1("Repairs by Manufacturer/Type/Model drill-down for manufacturers", style = {'textAlign': 'center'}),
        dcc.Link(html.Button("RETURN"), id="rbmtm_to_report_menu", href="/view_report_RBMTM/" + username, refresh=True),
        html.Table(children=[
            dbc.Container([
                dbc.Label('List for each manufacturer:'),
                html.Br(),
                dash_table.DataTable(
                    id='rbmtm_table',
                    columns=[{"name": "Type/Model" if i == "Type_Model" else i, "id": i} for i in df_rbmtm_drill.columns],
                    data=df_rbmtm_drill.to_dict('records'),
                    style_data_conditional=(
                        [
                            {
                                'if': {
                                    'filter_query': '{{Type_Model}} = {}'.format(i),
                                    'column_id': 'Type_Model'
                                },
                                'textAlign': 'left'
                            } for i in ['SUV', 'Car', 'Convertible', 'VanMinivan', 'Truck']
                        ] +
                        [
                            {
                                'if': {
                                    'filter_query': '{{Type_Model}} = {}'.format(i),
                                },
                                'background-color': 'WhiteSmoke',
                            } for i in ['SUV', 'Car', 'Convertible', 'VanMinivan', 'Truck']
                        ]
                    )
                )
            ]),
        ]),
    ])
    return repairs_by_MTM_drill_down
# View report end

@app.callback(
    dash.dependencies.Output('page-content', 'children'),
    [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    # Sales
    if pathname.startswith('/logged_in_sales') and pathname.split('/')[-2] == 'view_vehicle_detail':
        vin = pathname.split('/')[-1]
        username = pathname.split('/')[2]
        return layout_vehicle_details(vin, "Sales", username)
    elif pathname.startswith('/logged_in_sales') and pathname.split('/')[-3] == 'view_vehicle_detail' and pathname.endswith('sell'):
        vin = pathname.split('/')[-2]
        username = pathname.split('/')[2]
        return layout_sales_order_form(vin, username)
    elif pathname.startswith('/logged_in_sales') and 'add_individual_customer' in pathname.split('/')[-1]:
        vin = pathname.split('/')[-3]
        username = pathname.split('/')[2]
        driverlicense = pathname.split('/')[-1]
        driverlicense = driverlicense.replace("add_individual_customer_", "")
        return layout_sales_add_individual_customer(vin, username, driverlicense)
    elif pathname.startswith('/logged_in_sales') and 'add_business_customer' in pathname.split('/')[-1]:
        vin = pathname.split('/')[-3]
        username = pathname.split('/')[2]
        taxid = pathname.split('/')[-1]
        taxid = taxid.replace("add_business_customer_", "")
        return layout_sales_add_business_customer(vin, username, taxid)
    elif pathname.startswith('/logged_in_sales'):
        username = pathname.split('/')[-1]
        return layout_logged_in_sales(username)
    # repair
    elif pathname.startswith('/logged_in_service_writer'):
        username = pathname.split('/')[-1]
        return logged_in_service_writer(username)
    elif pathname.startswith('/repair_form_main_page'):
        username = pathname.split('/')[-1]
        return repair_form_main_page(username)
    elif pathname.startswith('/add_repair'):
        username = pathname.split('/')[-2]
        vin = pathname.split('/')[-1]
        return add_repair_layout(vin, username)
    elif pathname.startswith('/update_repair'):
        customerID = pathname.split('/')[-1]
        start_date = pathname.split('/')[-2]
        vin = pathname.split('/')[-3]
        username = pathname.split('/')[-4]
        return update_repair_layout(username, vin, start_date, customerID)
    elif pathname.startswith('/add_laborfee_part'):
        customerID = pathname.split('/')[-1]
        start_date = pathname.split('/')[-2]
        vin_value = pathname.split('/')[-3]
        username = pathname.split('/')[-4]
        return add_laborfee_parts_layout(username, vin_value, customerID, start_date)
    elif '/add_customer_ip' in pathname:
        ip_id = pathname.split('/')[-1]
        vin = pathname.split('/')[-2]
        username=pathname.split('/')[-3]
        return service_add_customer_ip_layout(username, vin, ip_id)
    elif '/add_customer_b' in pathname:
        tax_id = pathname.split('/')[-1]
        vin = pathname.split('/')[-2]
        username=pathname.split('/')[-3]
        return service_add_customer_b_layout(username, vin, tax_id)
    # inventory clerk start
    elif pathname.startswith('/logged_in_inventory_clerk'):
        [uname, passw] = get_uname_pass_from_path(pathname)
        return get_inventory_clerk_layout(uname, passw) if uname != "" else main_page()
    elif pathname.startswith('/add_vehicle'):
        [uname, passw] = get_uname_pass_from_path(pathname)
        return add_or_update_vehicle(uname, passw) if uname != "" else main_page()
    elif pathname.startswith('/add_type_details'):
        vt = input_vehicle_values['vehicle_type']
        [uname, passw] = get_uname_pass_from_path(pathname)
        return layout_vehicle_type_details(vt, uname, passw) if uname != "" else main_page()
    elif pathname.startswith('/inventory_clerk/show_details'):
        p = pathname.split('/')
        [uname, passw] = get_uname_pass_from_path(pathname)
        return layout_vehicle_details(p[-3], "Inventory", uname)
    # inventory clerk end
    # Manager
    elif pathname.startswith("/logged_in_manager/view_vehicle_detail/"):
        vin = pathname.split('/')[-1]
        return layout_vehicle_details(vin, "Manager", "")
    elif pathname.startswith('/logged_in_manager'):
        username = pathname.split('/')[-1]
        return get_logged_in_manager(username)
    elif pathname.startswith('/logged_in_admin'):
        username = pathname.split('/')[-1]
        return get_logged_in_admin(username)
    #view report start
    elif pathname.startswith('/view_report_SBC'):
        username = pathname.split('/')[-1]
        return get_salesbycolor(username)
    elif pathname.startswith('/view_report_SBT'):
        username = pathname.split('/')[-1]
        return get_salesbytype(username)
    elif pathname.startswith('/view_report_SBM'):
        username = pathname.split('/')[-1]
        return get_salesbymanufacturer(username)
    elif pathname.startswith('/view_report_GCI'):
        username = pathname.split('/')[-1]
        return get_gross_customer_income(username)
    elif pathname.startswith('/view_report_RBMTM'):
        username = pathname.split('/')[-1]
        return get_repairs_by_MTM(username)
    elif pathname.startswith('/gci_detail'):
        username = pathname.split('/')[-2]
        ID = pathname.split('/')[-1]
        return(get_detail_of_gi(ID, username))
    elif pathname.startswith('/drill_down'):
        manufacturer_name = pathname.split('/')[-1].replace('%20', ' ')
        username = pathname.split('/')[-2]
        return get_repair_drill_down(manufacturer_name, username)
    elif pathname.startswith('/view_report_BCS'):
        username = pathname.split('/')[-1]
        return get_belowcostsales(username)
    elif pathname.startswith('/view_report_ATII'):
        username = pathname.split('/')[-1]
        return get_averagetimeininventory(username)
    elif pathname.startswith('/view_report_PS'):
        username = pathname.split('/')[-1]
        return get_partsstatistics(username)
    elif pathname.startswith('/view_report_MS'):
        username = pathname.split('/')[-1]
        return get_monthly_sales(username)
    elif pathname.startswith('/view_report_monthly_result'):
        username = pathname.split('/')[-3]
        year = pathname.split('/')[-2]
        month = pathname.split('/')[-1]
        return get_monthly_sales_result(year, month, username)
#     elif pathname == '/view_report_None': 
#         return dcc.Location(href='/logged_in_manager', id='sales_order_page_b')
    #view report end
    elif pathname.startswith('/anonymous_view_vehicle_detail'):
        vin = pathname.split('/')[-1]
        return layout_vehicle_details(vin, "Anonymous", "")
    else:
        return main_page()


def main():
    # The reloader has not yet run - open the browser
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new('http://127.0.0.1:8050/')

    # Otherwise, continue as normal
    app.run_server(debug=True)


if __name__ == '__main__':
    main()
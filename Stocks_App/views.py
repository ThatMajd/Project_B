from django.shortcuts import render
from django.db import connection

from datetime import datetime
from Stocks_App.models import *



def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Create your views here.


def home(request):
    return render(request, 'home.html')


def query_results(request):
    with connection.cursor() as cursor:
        sql1 ="""
        SELECT Investor.Name, ROUND(total_sum,3) as 'ttlsum'
        FROM
        (SELECT k.ID, sum(TotalPrice) as 'total_sum'
        FROM
        (SELECT A.ID, (BQuantity * S.Price) AS 'TotalPrice'
        FROM
        (SELECT *
        FROM Buying
        WHERE Buying.ID in (SELECT ID from DiverseInvestors)) AS A
        INNER JOIN Stock AS S ON A.Symbol = S.Symbol AND A.tDate = S.tDate) AS K
        GROUP BY K.ID) as K1
        INNER JOIN Investor ON K1.ID = Investor.ID
        ORDER BY ttlsum DESC
        """
        sql2 ="""
        SELECT D.Symbol,Name,D.Total AS 'Quantity'
FROM
(SELECT *
FROM OwnpCompany

EXCEPT

SELECT A.ID,A.Symbol,A.Total
FROM OwnpCompany AS A
INNER JOIN OwnpCompany AS B ON A.Symbol = B.Symbol
WHERE A.Total < B.Total ) AS D
INNER JOIN Investor ON D.ID = Investor.ID
WHERE (D.Symbol IN (SELECT * FROM PopularCompanies)) AND (D.Total > 10)
ORDER BY D.Symbol,Name;
        """
        sql3 ="""SELECT Buying.tDate,Buying.Symbol,Name
FROM Buying
INNER JOIN cAuxTable cAT on Buying.Symbol = cAT.Symbol AND  Buying.tDate = cAT.tDate
INNER JOIN Investor I on I.ID = Buying.ID"""
        cursor.execute(sql1)
        sql_res1 = dictfetchall(cursor)

        cursor.execute(sql2)
        sql_res2 = dictfetchall(cursor)

        cursor.execute(sql3)
        sql_res3 = dictfetchall(cursor)

        return render(request, 'query_results.html', {
            'sql_res1': sql_res1,
            'sql_res2': sql_res2,
            'sql_res3': sql_res3
        })


def investor_exists(id1, cursor):
    sql = """
    SELECT COUNT(1) as 'res'
FROM Investor
WHERE ID = {};""".format(id1)
    cursor.execute(sql)
    res = dictfetchall(cursor)
    return res[0]['res']


def purchase_price(symbol, quantity, cursor):
    """
    Function gives the most recent stock price.
    Notice, function gives price stock when quantity = 1
    :param symbol:
    :param quantity:
    :param cursor:
    :return:
    """
    cursor.execute("""SELECT TOP(1)(%s * Price) as 'price'
FROM Stock
WHERE Symbol = %s
ORDER BY tDate DESC""", [quantity, symbol])
    price = dictfetchall(cursor)
    return price[0]['price']


def get_balance(id1, cursor):
    cursor.execute("""SELECT AvailableCash as 'Ac'
FROM Investor
WHERE ID = %s """, [id1])
    bal = dictfetchall(cursor)
    return bal[0]['Ac']


def can_buy(id1, price, cursor):
    if get_balance(id1, cursor) >= price:
        return 1
    return 0


def purchase_exists(id1, symbol, today, cursor):
    cursor.execute("""SELECT COUNT(1) AS 'res'
FROM Buying
WHERE ID=%s AND Symbol = %s AND tDate = %s """, [id1, symbol, today])
    res = dictfetchall(cursor)
    print(res)
    return res[0]['res']


def company_exists(symbol, cursor):
    cursor.execute("""SELECT COUNT(1) AS 'res'
FROM Company
WHERE Symbol=%s""", [symbol])
    res = dictfetchall(cursor)
    return res[0]['res']


def entry_exists(id1, today, cursor):
    sql = """SELECT COUNT(1) as 'res'
FROM Transactions
WHERE tDate = %s AND ID = %s"""
    cursor.execute(sql, [today, id1])
    res = dictfetchall(cursor)
    return res[0]['res']


def update_entry(id1, trnsc, today, cursor):
    # amount in transaction before updating
    sql = """SELECT TQuantity
FROM Transactions
WHERE tDate = %s AND ID = %s; """
    cursor.execute(sql, [today, id1])
    res = dictfetchall(cursor)
    amount = int(res[0]['TQuantity'])

    # getting current balance from investor
    sql = """SELECT AvailableCash
FROM Investor
WHERE ID = %s"""
    cursor.execute(sql, [id1])
    res = dictfetchall(cursor)
    prev_balance = int(res[0]['AvailableCash'])

    trnsc = int(trnsc)

    print(type(prev_balance))
    print(type(amount))
    print(type(trnsc))

    current_balance = prev_balance + amount - trnsc

    str(amount)
    str(prev_balance)

    # updating the balance
    sql = """UPDATE Investor
SET AvailableCash = %s
WHERE ID = %s;"""
    cursor.execute(sql, [current_balance, id1])

    # updating the transaction
    sql = """
    UPDATE Transactions
    SET TQuantity= %s
    WHERE tDate= %s AND ID = %s;
    """
    cursor.execute(sql, [trnsc, today, id1])


def transactions(request):
    msg = ""
    with connection.cursor() as cursor:
        if request.method == 'POST' and request.POST:

            id1 = request.POST["id"]
            today = datetime.today().strftime('%Y-%m-%d')
            trsnc = request.POST["transaction_sum"]
            if investor_exists(id1, cursor):
                if entry_exists(id1=id1, today=today, cursor=cursor):
                    update_entry(id1, trsnc, today, cursor)
                    msg = "An existing transaction has been updated!"
                else:
                    investor = Investor.objects.get(id=request.POST["id"])
                    new_content = Transactions(tdate=today,
                                               id=investor,
                                               tquantity=trsnc)
                    new_content.save()

                    sql = """SELECT AvailableCash
                    FROM Investor
                    WHERE ID = %s"""
                    cursor.execute(sql, [id1])
                    res = dictfetchall(cursor)
                    prev_balance = str(int(res[0]['AvailableCash']) - int(trsnc))

                    update_balance = """UPDATE Investor
                    SET AvailableCash = %s
                    WHERE ID = %s;"""
                    cursor.execute(update_balance, [prev_balance, id1])
                    msg = "New transaction has been added successfully!"

            else:
                msg = "Submitted Investor does not exist, Please try again!"

        cursor.execute("""SELECT TOP(10)*
FROM Transactions
ORDER BY tDate desc""")
        res_sql = dictfetchall(cursor)

        return render(request, 'transactions.html', {
            'msg': msg,
            'res_sql': res_sql
        })


def stock_exists(today, symbol, cursor):
    cursor.execute("""SELECT COUNT(1) as 'res'
FROM Stock
WHERE tDate = %s AND Symbol = %s """, [today, symbol])
    res = dictfetchall(cursor)
    return res[0]['res']


def buy_stock(today, id1, symbol, quantity, cursor):
    cmp = Company.objects.get(symbol=symbol)
    if stock_exists(today, symbol, cursor):
        stk = Stock.objects.get(symbol=symbol,
                                tdate=today)
    else:
        # create a stock
        # gets latest stock price
        s_price = purchase_price(symbol, 1, cursor)
        stk = Stock(symbol=cmp,
                    tdate=today,
                    price=s_price)
        stk.save(force_insert=True)
    # remove money from investors balance
    # assuming investor can afford the stock
    new_bal = str(int(get_balance(id1, cursor)) - (int(stk.price)*int(quantity)))
    cursor.execute("""UPDATE Investor
SET AvailableCash = %s
WHERE ID = %s """, [new_bal, id1])

    # add to buying relation
    cursor.execute("""INSERT INTO Buying(tDate, ID, Symbol, BQuantity)
VALUES (%s,%s,%s,%s) """, [today, id1, symbol, quantity])


def buy_stocks(request):
    with connection.cursor() as cursor:
        msg = ""
        smsg = ""
        cursor.execute("""SELECT TOP(10)S.tDate,ID,S.Symbol,ROUND((BQuantity*Price),3) AS 'Payed'
FROM Buying
INNER JOIN Stock S on S.Symbol = Buying.Symbol and S.tDate = Buying.tDate
ORDER BY Payed DESC , ID""")
        sql_res = dictfetchall(cursor)
        if request.method == 'POST' and request.POST:
            id1 = request.POST["id"]
            symbol = request.POST["company"]
            quantity = request.POST["quantity"]
            today = datetime.today().strftime('%Y-%m-%d')

            flag = 0

            if not investor_exists(id1, cursor):
                msg += "Investor does not exist \n"
                flag = 1
            if not company_exists(symbol, cursor):
                msg += "Company does not exist \n"
                flag = 1
            if flag == 0:
                price = purchase_price(symbol, quantity, cursor)
                if not can_buy(id1, price, cursor):
                    msg += "Investor can't afford this stock \n"
                else:
                    if purchase_exists(id1, symbol, today, cursor):
                        msg += "Purchase already exists for this investor \n"
                    else:
                        # Add buying thing
                        buy_stock(today, id1, symbol, quantity, cursor)
                        smsg += "{} shares of {} have been purchased by {} on {} successfully!\n".format(quantity,
                                                                                                         symbol,
                                                                                                         id1,
                                                                                                         today)
                        print('everything is fine')

            print(msg)
        return render(request, 'buy_stocks.html', {
            'smsg': smsg,
            'msg': msg,
            'sql_res': sql_res
        })

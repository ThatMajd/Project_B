---------------------------------------------------------------------------------------------------------------
                                                 -- QUESTION 1 --
---------------------------------------------------------------------------------------------------------------

CREATE VIEW DiverseInvestors AS
SELECT B.ID
FROM
(SELECT A.ID, MAX(A.cnt) as 'max'
FROM
(SELECT tDate,ID,COUNT(DISTINCT Sector) AS 'cnt'
FROM Buying inner join Company C on Buying.Symbol = C.Symbol
GROUP BY tDate,ID) AS A
GROUP BY A.ID) AS B
WHERE B.max >= 8


SELECT Investor.Name, ROUND(total_sum,3) as 'Total Sum'
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
ORDER BY [Total Sum] DESC



---------------------------------------------------------------------------------------------------------------
                                                 -- QUESTION 2 --
---------------------------------------------------------------------------------------------------------------
CREATE VIEW PopularCompanies AS
SELECT Symbol
    FROM
(SELECT A.Symbol, COUNT(A.tDate) AS 'cDays'
    FROM
(SELECT DISTINCT tDate,Symbol
FROM Buying) AS A
GROUP BY A.Symbol
)AS B,
(SELECT count(DISTINCT[tDate] ) AS 'maxDays'
FROM Buying) AS C
WHERE cDays > maxDays/2;


CREATE VIEW OwnpCompany AS
SELECT A.ID, A.Symbol, SUM(A.BQuantity) AS 'Total'
FROM
(SELECT Buying.tDate,ID,S.Symbol,BQuantity
FROM Buying
INNER JOIN Stock S on S.Symbol = Buying.Symbol and S.tDate = Buying.tDate) as A
GROUP BY A.ID, A.Symbol;


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



---------------------------------------------------------------------------------------------------------------
                                                 -- QUESTION 3 --
---------------------------------------------------------------------------------------------------------------



CREATE VIEW Temp AS
SELECT S1.Symbol AS 'Symbol1',S1.tDate AS 'tDay1',S1.Price AS 'Price1',
       S2.Symbol AS 'Symbol2',S2.tDate AS 'tDay2',S2.Price AS 'Price2',
       DATEDIFF(day,S1.tDate,S2.tDate) AS 'diff'
FROM
Stock AS S1
INNER JOIN
Stock AS S2 ON S1.Symbol=S2.Symbol
WHERE S1.tDate < S2.tDate;



CREATE VIEW cAuxTable AS
SELECT B.Symbol,S.tDate
FROM
    (SELECT A.Symbol
    FROM
        (SELECT Symbol, COUNT(*) AS 'num'
        FROM Buying
        GROUP BY Symbol) AS A
    WHERE num = 1) AS B
INNER JOIN Buying ON B.Symbol = Buying.Symbol
INNER JOIN Stock S on S.Symbol = Buying.Symbol and S.tDate = Buying.tDate

INTERSECT

SELECT Symbol1,tDay1
FROM
(SELECT *, (((Price2-Price1)/(Price1))*100) AS 'percentDelta'
FROM
(SELECT Symbol1,tDay1,Price1,Symbol2,tDay2,Price2
FROM Temp

EXCEPT

SELECT T2.Symbol1,T2.tDay1,T2.Price1,T2.Symbol2,T2.tDay2,T2.Price2
FROM Temp as T1
INNER JOIN Temp T2 on T1.Symbol1 = T2.Symbol1 AND T1.tDay1 = T2.tDay1
WHERE T1.diff < T2.diff) AS K) AS K2
WHERE percentDelta > 3;


SELECT Buying.tDate,Buying.Symbol,Name
FROM Buying
INNER JOIN cAuxTable cAT on Buying.Symbol = cAT.Symbol AND  Buying.tDate = cAT.tDate
INNER JOIN Investor I on I.ID = Buying.ID

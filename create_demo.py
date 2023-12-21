import functions as db
import pandas as pd

#https://pandas.pydata.org/docs/getting_started/intro_tutorials/02_read_write.html
users_df = pd.read_excel('BookDataset.xlsx', 'Users')
books_df = pd.read_excel('BookDataset.xlsx', 'Books')
ratings_df = pd.read_excel('BookDataset.xlsx', 'Book-Rating')
authors_df = pd.read_excel('BookDataset.xlsx', 'Authors')
#insert excel file data into the database sqlite

#https://youtu.be/0nI3HTLPpZI
#https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.itertuples.html
#https://stackoverflow.com/questions/43221208/iterate-over-pandas-dataframe-using-itertuples
#itertuples(): method generates an iterator object of the DataFrame, returning each row as a Pyton Tuple object, 
#and insert user at each row with its data.
#in my notes$$$$$$$$
for row in users_df.itertuples(index=False):
    db.ins_user(
        row[0],
        row[1],
        row[2],
        row[3],
        row[4],
        row[5],
        row[6],
        row[7]
    )

# insert books
for row in books_df.itertuples(index=False):
    db.ins_Book(
        row[0],
        row[1],
        row[2],
        row[3],
        row[4],
        row[5],
        row[6],
        row[7],
        row[8]
    )

# insert ratings
for row in ratings_df.itertuples(index=False):
   db.ins_Rate(row[0], row[1], row[2], row[3])

# insert authors
for row in authors_df.itertuples(index=False):
   db.ins_author(row[0], row[1])

print("Done!")
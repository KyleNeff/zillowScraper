from flask import Flask, request, render_template
import mysql.connector
import mainScraper
import csvToSQL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Connect to MySQL database
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="MusicRecPassword",
        database="zillowscraping"
    )
    return connection

# Home Page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get Location and Order Option
        location = request.form['location']
        sort_option = request.form.get('sort', 'price_asc')

        scraper = mainScraper.ZillowScraper()

        try:
            print(f"Running scraper for location: {location}")
            scraper.run(location)
            scraper.close()
        except Exception as e:
            return f"Error running scraper: {e}"

        # Add csvfile into SQL Database
        try:
            csvToSQL.csvToSQLDatabase(location)
        except Exception as e:
            return f"Error inserting data into database: {e}"

        # Normalize table names
        table_name = location.replace('-', '_')
        
        sql_query = f"SELECT *, price / floorSize AS price_per_sqft FROM {table_name}"

        # Dropdown options, add Order by to end of SQL statement
        if sort_option == 'price_asc':
            sql_query += " ORDER BY price ASC;"
        elif sort_option == 'price_desc':
            sql_query += " ORDER BY price DESC;"
        elif sort_option == 'floorSize_asc':
            sql_query += " ORDER BY floorSize ASC;"
        elif sort_option == 'floorSize_desc':
            sql_query += " ORDER BY floorSize DESC;"
        elif sort_option == 'price_per_sqft_asc':
            sql_query += " ORDER BY price / floorSize ASC;"
        elif sort_option == 'price_per_sqft_desc':
            sql_query += " ORDER BY price / floorSize DESC;"

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                results = cursor.fetchall()
        except mysql.connector.Error as err:
            return f"Database error: {err}"
        finally:
            connection.close()

        # Render results and HTML
        return render_template('index.html', comments=results)

    # Render form in GET Request
    return render_template('index.html', comments=[])


if __name__ == "__main__":
    app.run(port=5000, debug=True)

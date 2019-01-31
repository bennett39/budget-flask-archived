import sqlalchemy
#  import urllib import parse
#  import psycopg2

#  def Postgres():
    #  parse.uses_netloc.append("postgres")
    #  url = urlparse.urlparse(os.environ["DATABASE_URL"])
    #  return psycopg2.connect(
        #  database=url.path[1:],
        #  user=url.username,
        #  password=url.password,
        #  host=url.hostname,
        #  port=url.port
    #  )


class SQL(object):
    def __init__(self, url):
        try:
            self.engine = sqlalchemy.create_engine(url)
        except Exception as e:
            raise RuntimeError(e)

    def execute(self, text, *multiparams, **params):
        try:
            statement = sqlalchemy.text(text).bindparams(*multiparams, **params)
            result = self.engine.execute(str(statement.compile(compile_kwargs={"literal_binds": True})))
            # SELECT
            if result.returns_rows:
                rows = result.fetchall()
                return [dict(row) for row in rows]
            # INSERT
            elif result.lastrowid is not None:
                return result.lastrowid
            # DELETE, UPDATE
            else:
                return result.rowcount 
        except sqlalchemy.exc.IntegrityError:
            return None
        except Exception as e:
            raise RuntimeError(e)

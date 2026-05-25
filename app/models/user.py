from app.database import execute_query


class User:

    def __init__(self, id=None, full_name=None, email=None, password=None):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.password = password

    @classmethod
    def get_by_id(cls, user_id):
        query = """
            SELECT * FROM users
            WHERE id = %s
        """

        results = execute_query(
            query,
            (user_id,),
            fetch=True
        )

        if results:
            user = results[0]

            return cls(
                id=user['id'],
                full_name=user['full_name'],
                email=user['email'],
                password=user.get('password')
            )

        return None

    @classmethod
    def get_by_email(cls, email):
        query = """
            SELECT * FROM users
            WHERE email = %s
        """

        results = execute_query(
            query,
            (email,),
            fetch=True
        )

        if results:
            user = results[0]

            return cls(
                id=user['id'],
                full_name=user['full_name'],
                email=user['email'],
                password=user.get('password')
            )

        return None

    def save(self):
        query = """
            INSERT INTO users
            (full_name, email, password)
            VALUES (%s, %s, %s)
        """

        return execute_query(
            query,
            (
                self.full_name,
                self.email,
                self.password
            )
        )

    def update_profile(self):
        query = """
            UPDATE users
            SET full_name = %s
            WHERE id = %s
        """

        return execute_query(
            query,
            (
                self.full_name,
                self.id
            )
        )

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email
        }
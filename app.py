from flask import Flask
from flask_graphql import GraphQLView

from graphene import (
    ObjectType,
    String,
    Int,
    Schema,
    ID,
    Field,
    List,
    Mutation,
    InputObjectType
)
import json

# load data from json
json_data = {}
with open('./test_data.json') as json_file:
    json_data = json.load(json_file)

USERS_DATA = json_data['users']
COMPANIES_DATA = json_data['companies']


class Model:
    def __init__(self, storage):
        self.storage = storage

    def get_by_id(self, id):
        res = list(filter(lambda x: x['id'] == id, self.storage))
        if len(res) < 1:
            return None
        return res[0]

    def search_idx(self, key, value):
        idx = None
        for i, val in enumerate(self.storage):
            if val[key] == value:
                idx = i
                break
        return idx

    def update_attr(self, id, key, new_value):
        el_idx = self.search_idx('id', id)
        if el_idx is None:
            return

        self.storage[el_idx][key] = new_value

    def get_all(self):
        return self.storage


class UserModel(Model):
    def __init__(self, storage):
        super().__init__(storage)

    def create(self, data):
        last_id = self.storage[-1]['id']
        new_id = last_id + 1

        new_user = {
            'id': new_id,
            'name': data['name'],
            'age': data['age'],
            'works_at': data['works_at']
        }

        self.storage.append(new_user)
        return new_id


class CompanyModel(Model):
    def __init__(self, storage):
        super().__init__(storage)

    def create(self, data):
        last_id = self.storage[-1]['id']

        new_company = {
            'id': last_id + 1,
            'name': data['name']
        }

        self.storage.append(new_company)


users_model = UserModel(USERS_DATA)
companies_model = CompanyModel(COMPANIES_DATA)


class CompanyNode(ObjectType):
    id = ID()
    name = String()


class UserNode(ObjectType):
    id = Int()
    name = String()
    age = Int()
    works_at = Int()
    company = Field(CompanyNode)

    def resolve_company(_, info):
        company = companies_model.get_by_id(_.works_at)
        return CompanyNode(id=_.works_at, name=company.get('name', ''))


class UserInput(InputObjectType):
    name = String(required=True)
    age = Int(required=True)
    works_at = Int(required=True)


class CreateUser(Mutation):

    class Arguments:
        user_data = UserInput(required=True)

    Output = UserNode

    def mutate(_, info, user_data=None):

        id = users_model.create({
            'name': user_data.name,
            'age': user_data.age,
            'works_at': user_data.works_at
        })

        return UserNode(
            id=id,
            name=user_data.name,
            age=user_data.age,
            works_at=user_data.works_at
        )


class Mutations(ObjectType):
    create_user = CreateUser.Field()


class Query(ObjectType):
    hello = String()
    user = Field(UserNode, id=Int(required=True))
    all_users = List(UserNode)

    def resolve_hello(_, info):
        return 'Hello, working here'

    def resolve_user(_, info, id):
        user = users_model.get_by_id(id)
        return UserNode(id=user['id'], name=user['name'], age=user['age'], works_at=user['works_at'])

    def resolve_all_users(_, info):
        users = users_model.get_all()
        users_res = []
        for user in users:
            users_res.append(UserNode(
                id=user['id'],
                name=user['name'],
                age=user['age'],
                works_at=user['works_at']
            ))

        return users_res


schema = Schema(query=Query, mutation=Mutations)


app = Flask(__name__)
app.debug = True


@app.route('/', methods=['GET'])
def index():
    return "Service UP"


app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
    'graphql',
    schema=schema,
    graphiql=True
))


if __name__ == '__main__':
    app.run()




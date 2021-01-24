import collections
import logging

#Credit to menudocs for some of the code here

class MongoDB:
    def __init__(self, connection, document_name):
        self.db = connection[document_name]
        self.logger = logging.getLogger(__name__)

    async def update(self, dict):
        await self.update_by_id(dict)

    async def get_by_id(self, id):
        return await self.find_by_id(id)

    async def find(self, id):
        return await self.find_by_id(id)

    async def delete(self, id):
        await self.delete_by_id(id)

    async def find_by_id(self, id):
        return await self.db.find_one({"_id": id})

    async def delete_by_id(self, id):
        if not await self.find_by_id(id):
            return

        await self.db.delete_many({"_id": id})

    async def insert(self, dict):
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected a dictionary.")
        if not dict["_id"]:
            raise KeyError("_id not couldn't be found in given dictionary.")
        await self.db.insert_one(dict)
    async def upsert(self, dict):
        if await self.__get_raw(dict["_id"]) != None:
            await self.update_by_id(dict)
        else:
            await self.db.insert_one(dict)

    async def update_by_id(self, dict):
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected a dictionary.")

        # Always use your own _id
        if not dict["_id"]:
            raise KeyError("_id not couldn't be found in given dictionary.")

        if not await self.find_by_id(dict["_id"]):
            return

        id = dict["_id"]
        dict.pop("_id")
        await self.db.update_one({"_id": id}, {"$set": dict})

    async def unset(self, dict):
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected a dictionary.")
        if not dict["_id"]:
            raise KeyError("_id not couldn't be found in given dictionary.")

        if not await self.find_by_id(dict["_id"]):
            return

        id = dict["_id"]
        dict.pop("_id")
        await self.db.update_one({"_id": id}, {"$unset": dict})

    async def increment(self, id, amount, field):
        if not await self.find_by_id(id):
            return

        await self.db.update_one({"_id": id}, {"$inc": {field: amount}})

    async def get_all(self):
        data = []
        async for document in self.db.find({}):
            data.append(document)
        return data

    async def __get_raw(self, id):
        return await self.db.find_one({"_id": id})
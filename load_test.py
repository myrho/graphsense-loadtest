#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from random import choice, randint

from locust import HttpUser, task, between
from locust.exception import RescheduleTaskImmediately

CURRENCY = "btc"
MIN_BLOCK = 1


class UserBehavior(HttpUser):
    wait_time = between(0.5, 5)

    def on_start(self):
        self.addresses = []
        self.txs = []
        self.entities = []
        self.max_block = 0
        self.taxonomies_ = []

    def fetch(self, url, name=None):
        print(f'request {url}')
        response = self.client.get(url, name=name)
        try:
            assert response.ok
            result = json.loads(response.content)
        except AssertionError:
            print(f'request {url}, response {response.content}')
            raise RescheduleTaskImmediately()

        # keep stored things short
        self.addresses = self.addresses[-1000:]
        self.txs = self.txs[-1000:]
        self.entities = self.entities[-1000:]

        return result

    @task
    def stats(self):
        stats = self.fetch("/stats")
        for stat in stats['currencies']:
            if stat['name'] == CURRENCY:
                self.max_block = stat['no_blocks'] - 1
                break

    @task
    def block(self):
        if not self.max_block:
            raise RescheduleTaskImmediately()
        height = randint(MIN_BLOCK, self.max_block)
        url = "/{CURRENCY}/blocks/{height}"
        self.fetch(url.format(CURRENCY=CURRENCY, height=height), url)

    @task
    def block_txs(self):
        if not self.max_block:
            raise RescheduleTaskImmediately()
        height = randint(MIN_BLOCK, self.max_block)
        url = "/{CURRENCY}/blocks/{height}/txs"
        response = self.fetch(url.format(CURRENCY=CURRENCY, height=height),
                              url)

        for tx in response:
            self.txs.append(tx['tx_hash'])

    @task
    def transaction(self):
        if not self.txs:
            raise RescheduleTaskImmediately()

        tx = choice(self.txs)
        url = "/{CURRENCY}/txs/{tx}"
        response = self.fetch(url.format(CURRENCY=CURRENCY, tx=tx), url)
        for elem in response["outputs"]:
            for address in elem['address']:
                self.addresses.append(address)

        for elem in response['inputs']:
            for address in elem['address']:
                self.addresses.append(address)

    @task
    def exchange_rates(self):
        if not self.max_block:
            raise RescheduleTaskImmediately()
        height = randint(MIN_BLOCK, self.max_block)
        url = "/{CURRENCY}/rates/{height}"
        self.fetch(url.format(CURRENCY=CURRENCY, height=height), url)

    @task
    def taxonomies(self):
        response = self.fetch("/tags/taxonomies")
        self.taxonomies = [tax['taxonomy'] for tax in response]

    @task
    def concepts(self):
        if not self.taxonomies_:
            raise RescheduleTaskImmediately()

        taxo = choice(self.taxonomies_)
        url = "/tags/taxonomies/{taxo}/concepts"
        self.fetch(url.format(CURRENCY=CURRENCY, taxo=taxo), url)

    @task
    def address_entity(self):
        if not self.addresses:
            raise RescheduleTaskImmediately()

        address = choice(self.addresses)
        url = "/{CURRENCY}/addresses/{address}/entity"

        response = self.fetch(url.format(CURRENCY=CURRENCY, address=address),
                              url)
        self.entities.append(response['entity'])

    @task
    def nodes(self):
        node_type = choice(["addresses", "entities"])

        url = f"/{{CURRENCY}}/{node_type}"
        response = self.fetch(url.format(CURRENCY=CURRENCY), url)

        ntype = 'address' if node_type == 'addresses' else 'entity'
        for node in response[node_type]:
            getattr(self, node_type).append(node[ntype])

    @task
    def node(self):
        node_type = choice(["addresses", "entities"])

        pool = getattr(self, node_type)

        if not pool:
            raise RescheduleTaskImmediately()

        node = choice(pool)

        url = f"/{{CURRENCY}}/{node_type}/{{node}}"
        response = self.fetch(url.format(CURRENCY=CURRENCY, node=node), url)

        if node_type == 'addresses':
            self.entities.append(response['entity'])

    @task
    def address_txs(self):
        if not self.addresses:
            raise RescheduleTaskImmediately()

        node = choice(self.addresses)

        url = "/{CURRENCY}/addresses/{node}/txs"
        response = self.fetch(url.format(CURRENCY=CURRENCY, node=node),
                              url)
        for tx in response['txs']:
            self.txs.append(tx['tx_hash'])

    @task
    def address_links(self):
        if not self.addresses:
            raise RescheduleTaskImmediately()

        node = choice(self.addresses)
        neighbor = choice(self.addresses)

        url = "/{CURRENCY}/addresses/{node}/links?neighbor={neighbor}"
        response = self.fetch(url.format(
            CURRENCY=CURRENCY, node=node, neighbor=neighbor),
            url)
        for tx in response:
            self.txs.append(tx['tx_hash'])

    @task
    def node_tags(self):
        node_type = choice(["addresses", "entities"])

        pool = getattr(self, node_type)

        if not pool:
            raise RescheduleTaskImmediately()

        node = choice(pool)

        url = f"/{{CURRENCY}}/{node_type}/{{node}}/tags"
        response = self.fetch(url.format(CURRENCY=CURRENCY, node=node), url)
        if node_type == 'entities':
            for tag in response['entity_tags']:
                self.entity_tags.append(tag['label'])
        else:
            for tag in response:
                self.address_tags.append(tag['label'])

    @task
    def node_neighbors(self):
        node_type = choice(["addresses", "entities"])

        pool = getattr(self, node_type)

        if not pool:
            raise RescheduleTaskImmediately()

        node = choice(pool)

        direction = choice(['in', 'out'])

        url = (f"/{{CURRENCY}}/{node_type}/{{node}}"
               f"/neighbors?direction={direction}")
        response = self.fetch(url.format(CURRENCY=CURRENCY, node=node), url)

        for neighbor in response['neighbors']:
            getattr(self, node_type).append(neighbor['id'])

    @task
    def entity_address(self):
        if not self.entities:
            raise RescheduleTaskImmediately()

        entity = choice(self.entities)
        url = "/{CURRENCY}/entities/{entity}/addresses"
        response = self.fetch(url.format(CURRENCY=CURRENCY, entity=entity),
                              url)

        for address in response['addresses']:
            self.addresses.append(address['address'])

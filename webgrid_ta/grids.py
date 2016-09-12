from __future__ import absolute_import
from webgrid import BaseGrid as BaseGrid, Column, LinkColumnBase, \
    YesNoColumn, DateTimeColumn, DateColumn, NumericColumn
from webgrid.filters import TextFilter, OptionsFilterBase, Operator, \
    DateTimeFilter, ops
from .model.entities import ArrowRecord, Person, Status

from .app import webgrid


class Grid(BaseGrid):
    manager = webgrid


class FirstNameColumn(LinkColumnBase):
    def create_url(self, record):
        return '/person-edit/{0}'.format(record.id)


class FullNameColumn(LinkColumnBase):
    def extract_data(self, record):
        return '{0.firstname} {0.lastname}'.format(record)

    def create_url(self, record):
        return '/person-edit/{0}'.format(record.id)


class EmailsColumn(Column):
    def extract_data(self, recordset):
        return ', '.join([e.email for e in recordset.Person.emails])


class StatusFilter(OptionsFilterBase):
    operators = (
        Operator('o', 'open', None),
        ops.is_,
        ops.not_is,
        Operator('c', 'closed', None),
        ops.empty,
        ops.not_empty
    )
    options_from = Status.pairs


class PeopleGrid(Grid):
    session_on = True

    FirstNameColumn('First Name', Person.firstname, TextFilter)
    FullNameColumn('Full Name')
    YesNoColumn('Active', Person.inactive, reverse=True)
    EmailsColumn('Emails')
    Column('Status', Status.label.label('status'), StatusFilter(Status.id))
    DateTimeColumn('Created', Person.createdts, DateTimeFilter)
    DateColumn('Due Date', 'due_date')
    Column('Sort Order', Person.sortorder, render_in='xls')
    NumericColumn('Number', Person.numericcol, has_subtotal=True)

    def query_prep(self, query, has_sort, has_filters):
        query = query.add_columns(
            Person.id, Person.lastname, Person.due_date
        ).add_entity(Person).outerjoin(Person.status)

        # default sort
        if not has_sort:
            query = query.order_by(Person.id)

        return query


class ArrowGrid(Grid):
    session_on = True

    DateTimeColumn('Created', ArrowRecord.created_utc, DateTimeFilter)

    def query_prep(self, query, has_sort, has_filters):
        # default sort
        if not has_sort:
            query = query.order_by(ArrowRecord.id)

        return query

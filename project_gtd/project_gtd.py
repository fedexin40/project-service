# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp import tools


class project_gtd_context(osv.Model):
    _name = "project.gtd.context"
    _description = "Context"
    _columns = {
        'name': fields.char(
            'Context', size=64, required=True, translate=True),
        'sequence': fields.integer(
            'Sequence',
            help=("Gives the sequence order when displaying "
                  "a list of contexts.")),
    }
    _defaults = {
        'sequence': 1
    }
    _order = "sequence, name"


class project_gtd_timebox(osv.Model):
    _name = "project.gtd.timebox"
    _order = "sequence"
    _columns = {
        'name': fields.char(
            'Timebox', size=64, required=True, select=1, translate=1),
        'sequence': fields.integer(
            'Sequence',
            help="Gives the sequence order when displaying "
                 "a list of timebox."),
    }


class project_task(osv.Model):
    _inherit = "project.task"
    _columns = {
        'timebox_id': fields.many2one(
            'project.gtd.timebox',
            "Timebox",
            help="Time-laps during which task has to be treated"),
        'context_id': fields.many2one(
            'project.gtd.context',
            "Context",
            help="The context place where user has to treat task"),
    }

    def _get_context(self, cr, uid, context=None):
        ids = self.pool.get('project.gtd.context').search(
            cr, uid, [], context=context)
        return ids and ids[0] or False

    def _read_group_timebox_ids(
            self, cr, uid, ids, domain,
            read_group_order=None, access_rights_uid=None, context=None):
        """Used to display all timeboxes on the view."""
        print read_group_order, access_rights_uid
        timebox_obj = self.pool.get('project.gtd.timebox')
        order = timebox_obj._order
        access_rights_uid = access_rights_uid or uid
        timebox_ids = timebox_obj._search(
            cr, uid, [],
            order=order, access_rights_uid=access_rights_uid, context=context)
        result = timebox_obj.name_get(
            cr, access_rights_uid, timebox_ids, context=context)
        # Restore order of the search
        result.sort(
            lambda x, y: cmp(timebox_ids.index(x[0]), timebox_ids.index(y[0])))
        fold = dict.fromkeys(timebox_ids, False)
        return result, fold

    _defaults = {
        'context_id': _get_context
    }

    _group_by_full = {
        'timebox_id': _read_group_timebox_ids,
    }

    def copy_data(self, cr, uid, id, default=None, context=None):
        if context is None:
            context = {}
        if not default:
            default = {}
        default['timebox_id'] = False
        default['context_id'] = False
        return super(project_task, self).copy_data(
            cr, uid, id, default, context)

    def next_timebox(self, cr, uid, ids, *args):
        timebox_obj = self.pool.get('project.gtd.timebox')
        timebox_ids = timebox_obj.search(cr, uid, [])
        if not timebox_ids:
            return True
        for task in self.browse(cr, uid, ids):
            timebox = task.timebox_id
            if not timebox:
                self.write(cr, uid, task.id, {'timebox_id': timebox_ids[0]})
            elif timebox_ids.index(timebox) != len(timebox_ids)-1:
                index = timebox_ids.index(timebox)
                self.write(
                    cr, uid, task.id, {'timebox_id': timebox_ids[index+1]})
        return True

    def prev_timebox(self, cr, uid, ids, *args):
        timebox_obj = self.pool.get('project.gtd.timebox')
        timebox_ids = timebox_obj.search(cr, uid, [])
        for task in self.browse(cr, uid, ids):
            timebox = task.timebox_id
            if timebox:
                if timebox_ids.index(timebox):
                    index = timebox_ids.index(timebox)
                    self.write(
                        cr, uid, task.id,
                        {'timebox_id': timebox_ids[index - 1]})
                else:
                    self.write(cr, uid, task.id, {'timebox_id': False})
        return True

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if not context:
            context = {}
        res = super(project_task, self).fields_view_get(
            cr, uid, view_id, view_type, context,
            toolbar=toolbar, submenu=submenu)
        search_extended = False
        timebox_obj = self.pool.get('project.gtd.timebox')
        if (res['type'] == 'search') and context.get('gtd', False):
            timeboxes = timebox_obj.browse(
                cr, uid, timebox_obj.search(cr, uid, []), context=context)
            search_extended = ''
            for timebox in timeboxes:
                filter_ = u"""
                    <filter domain="[('timebox_id', '=', {timebox_id})]"
                            string="{string}"/>\n
                    """.format(timebox_id=timebox.id, string=timebox.name)
                search_extended += filter_
            search_extended += '<separator orientation="vertical"/>'
            res['arch'] = tools.ustr(res['arch']).replace(
                '<separator name="gtdsep"/>', search_extended)

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

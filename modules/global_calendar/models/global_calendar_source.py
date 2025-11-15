# -*- coding: utf-8 -*-
import logging
from ast import literal_eval
from datetime import datetime, time, timedelta

import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger("GLOBAL_CALENDAR")

HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")

class GlobalCalendarSource(models.Model):
    _name = "global.calendar.source"
    _description = "Global Calendar Source"
    _order = "sequence, id"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    # Palette legacy (laisse en place pour compat rétro)
    color_index = fields.Integer(string='Color (palette index)', default=0, help='0..11')

    # Couleur libre (hex)
    color_hex = fields.Char(string='Color', default='#3a53bb', help='Hex #RRGGBB')

    # Modèle ciblé
    model_id = fields.Many2one("ir.model", string="Model", required=True, ondelete="cascade")

    # Mapping champs
    title_field_id = fields.Many2one(
        "ir.model.fields", ondelete="set null",
        string="Title Field",
        domain="[('model_id','=',model_id), ('ttype','in',('char','text','many2one'))]",
    )
    start_field_id = fields.Many2one(
        "ir.model.fields", ondelete="cascade",
        string="Start Field",
        required=True,
        domain="[('model_id','=',model_id), ('ttype','in',('date','datetime'))]",
    )
    stop_field_id = fields.Many2one(
        "ir.model.fields", ondelete="set null",
        string="Stop Field",
        domain="[('model_id','=',model_id), ('ttype','in',('date','datetime'))]",
    )

    
    # Champ de durée optionnel : indique le champ numérique (float/int) du modèle source
    # qui contient une durée (en heures). Utilisé uniquement si le Stop Field est vide/absent.
    duration_field_id = fields.Many2one(
        "ir.model.fields",
        ondelete="set null",
        string="Duration Field",
        domain="[('model_id','=',model_id), ('ttype','in',('float','integer'))]",
        help="Champ numérique (float/int) représentant la durée (en heures) à appliquer si Stop est absent."
    )



    # Champ(s) utilisateur
    user_m2o_field_id = fields.Many2one(
        "ir.model.fields", ondelete="set null",
        string="User (many2one)",
        domain="[('model_id','=',model_id), ('ttype','=','many2one'), ('relation','=','res.users')]",
    )
    user_m2m_field_id = fields.Many2one(
        "ir.model.fields", ondelete="set null",
        string="Users (many2many)",
        domain="[('model_id','=',model_id), ('ttype','=','many2many'), ('relation','=','res.users')]",
    )

    # Filtre domaine
    domain_filter = fields.Text(string="Domain")

    # Visibilité
    visible_to_everyone = fields.Boolean(string="Visible to everyone (fallback)", default=False)

    last_sync = fields.Datetime(readonly=True)
    sync_chunk_size = fields.Integer(default=1000)

    # -------------------------
    # Validations / Logging
    # -------------------------
    @api.constrains('color_hex')
    def _check_color_hex(self):
        for rec in self:
            if rec.color_hex and not HEX_RE.match(rec.color_hex):
                raise UserError(_("Invalid hex color. Use #RRGGBB."))

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        _logger.warning(
            "[GLOBAL_CALENDAR][SOURCE][CREATE] id=%s name=%s model=%s color_hex=%s color_index=%s",
            rec.id, rec.name, rec.model_id.model, rec.color_hex, rec.color_index
        )
        return rec

    def write(self, vals):
        for rec in self:
            before_hex = rec.color_hex
            before_idx = rec.color_index
            before_model = rec.model_id.model
            before_name = rec.name
        res = super().write(vals)
        for rec in self:
            after_hex = rec.color_hex
            after_idx = rec.color_index
            if ('color_hex' in vals and before_hex != after_hex) or ('color_index' in vals and before_idx != after_idx):
                _logger.warning(
                    "[GLOBAL_CALENDAR][SOURCE][COLOR_CHANGE] id=%s name=%s model=%s hex:%s->%s idx:%s->%s",
                    rec.id, (vals.get('name') or before_name), (rec.model_id.model or before_model),
                    before_hex, after_hex, before_idx, after_idx
                )
        return res

    # -------------------------

    def _parse_domain(self):
        if not self.domain_filter:
            return []
        try:
            return safe_eval(self.domain_filter.strip())
        except Exception:
            try:
                return literal_eval(self.domain_filter.strip())
            except Exception as e:
                raise UserError(_("Invalid domain: %s") % e)

    def _field_value(self, record, field):
        return getattr(record, field.name) if field else False

    def _to_datetime(self, value, is_stop=False):
        if not value:
            return False, False
        if isinstance(value, str):
            try:
                dt = fields.Datetime.from_string(value)
                return dt, False
            except Exception:
                d = fields.Date.from_string(value)
                if not is_stop:
                    return datetime.combine(d, time.min), True
                return datetime.combine(d, time.max), True
        elif hasattr(value, "hour"):
            return value, False
        else:
            if not is_stop:
                return datetime.combine(value, time.min), True
            return datetime.combine(value, time.max), True

    def _title_from_record(self, record, title_field):
        if not title_field:
            return record.display_name or getattr(record, "name", False) or record._name
        val = getattr(record, title_field.name)
        if title_field.ttype == "many2one":
            return val.display_name if val else record.display_name or record._name
        return val or record.display_name or record._name

    def action_sync(self):
        for source in self:
            # _logger.warning("[GLOBAL_CALENDAR][SYNC][BEGIN] source_id=%s model=%s", source.id, source.model_id.model)
            source._sync_source()
            # _logger.warning("[GLOBAL_CALENDAR][SYNC][END] source_id=%s model=%s last_sync=%s", source.id, source.model_id.model, source.last_sync)
        return True

    @api.model
    def cron_sync_all_sources(self):
        sources = self.search([("active", "=", True)])
        for source in sources:
            # _logger.warning("[GLOBAL_CALENDAR][CRON_SYNC] source_id=%s model=%s", source.id, source.model_id.model)
            source._sync_source()

    def _sync_source(self):
        self.ensure_one()
        Model = self.env[self.model_id.model]
        domain = self._parse_domain()

        existing = self.env["global.calendar.event"].search([
            ("model_name", "=", self.model_id.model),
        ])
        existing_by_res = {e.res_id: e for e in existing}

        offset = 0
        limit = max(1, self.sync_chunk_size)
        seen = set()
        created = 0
        updated = 0

        # _logger.warning(
        #     "[GLOBAL_CALENDAR][SYNC][SCAN] source_id=%s model=%s domain=%s batch=%s",
        #     self.id, self.model_id.model, domain, limit
        # )

        while True:
            batch = Model.search(domain, offset=offset, limit=limit, order="id asc")
            if not batch:
                break
            for rec in batch:
                start_raw = self._field_value(rec, self.start_field_id)
                stop_raw = self._field_value(rec, self.stop_field_id) if self.stop_field_id else False
                start_dt, start_all_day = self._to_datetime(start_raw, is_stop=False)
                #stop_dt, stop_all_day = self._to_datetime(stop_raw, is_stop=True) if stop_raw else (start_dt, start_all_day)
                stop_dt, stop_all_day = (self._to_datetime(stop_raw, is_stop=True) if stop_raw else (False, False))
                
                # Fallback: si pas de stop, on tente la durée depuis duration_field_id (en heures)
                if not stop_dt:
                    dur_val = False
                    if self.duration_field_id:
                        try:
                            dur_val = self._field_value(rec, self.duration_field_id)
                        except Exception:
                            dur_val = False
                    try:
                        dur = float(dur_val) if dur_val is not False and dur_val is not None else 0.0
                    except Exception:
                        dur = 0.0

                    if start_dt and dur > 0.0:
                        stop_dt = start_dt + timedelta(hours=dur)
                        stop_all_day = False
                    else:
                        # dernier recours: événement instantané (comportement historique)
                        stop_dt, stop_all_day = start_dt, start_all_day

                if not start_dt:
                    continue

                title = self._title_from_record(rec, self.title_field_id)

                user_ids = []
                if self.user_m2o_field_id:
                    u = self._field_value(rec, self.user_m2o_field_id)
                    if u:
                        user_ids.append(u.id)
                if self.user_m2m_field_id:
                    usets = self._field_value(rec, self.user_m2m_field_id)
                    if usets:
                        user_ids.extend(usets.ids)
                user_ids = list(sorted(set(user_ids)))
                allow_all = self.visible_to_everyone if not user_ids else False

                vals = {
                    "name": title,
                    "start": start_dt,
                    "stop": stop_dt,
                    "all_day": bool(start_all_day or stop_all_day),
                    "user_ids": [(6, 0, user_ids)],
                    "allow_all_users": allow_all,
                    "source_id": self.id,
                    "model_name": self.model_id.model,
                    "res_id": rec.id,
                }

                ev = existing_by_res.get(rec.id)
                if ev:
                    ev.write(vals)
                    updated += 1
                    # _logger.warning(
                    #     "[GLOBAL_CALENDAR][SYNC][UPDATE] event_id=%s res=%s model=%s title=%s src_hex=%s src_idx=%s",
                    #     ev.id, rec.id, self.model_id.model, title, self.color_hex, self.color_index
                    # )
                else:
                    ev = self.env["global.calendar.event"].create(vals)
                    existing_by_res[rec.id] = ev
                    created += 1
                    # _logger.warning(
                    #     "[GLOBAL_CALENDAR][SYNC][CREATE] event_id=%s res=%s model=%s title=%s src_hex=%s src_idx=%s",
                    #     ev.id, rec.id, self.model_id.model, title, self.color_hex, self.color_index
                    # )
                seen.add(rec.id)

            offset += limit

        to_unlink = self.env["global.calendar.event"].search([
            ("model_name", "=", self.model_id.model),
            ("res_id", "not in", list(seen) or [0]),
        ])
        removed = len(to_unlink)
        if removed:
            # _logger.warning(
            #     "[GLOBAL_CALENDAR][SYNC][CLEANUP] source_id=%s model=%s removed=%s",
            #     self.id, self.model_id.model, removed
            # )
            to_unlink.unlink()

        self.last_sync = fields.Datetime.now()
        # _logger.warning(
        #     "[GLOBAL_CALENDAR][SYNC][SUMMARY] source_id=%s created=%s updated=%s removed=%s",
        #     self.id, created, updated, removed
        # )

    def action_open_events(self):
        self.ensure_one()
        action = self.env.ref("global_calendar.action_global_calendar_event").read()[0]
        action["domain"] = [("source_id", "=", self.id)]
        return action

    @api.model
    def action_bootstrap_common_sources(self):
        def model_exists(model):
            return bool(self.env['ir.model'].sudo().search([('model', '=', model)], limit=1))
        def field_id(model, name):
            return self.env['ir.model.fields'].sudo().search([('model', '=', model), ('name', '=', name)], limit=1).id
        def first_existing_field_id(model, candidates):
            for n in candidates:
                fid = field_id(model, n)
                if fid:
                    return fid
            return False

        requested = [
            dict(name="CRM Opportunities", model="crm.lead",
                 title="name", start=["date_deadline"], stop=[],
                 user_m2o="user_id", user_m2m=None),
            dict(name="Project Tasks", model="project.task",
                 title="name", start=["date_deadline"], stop=[],
                 user_m2o="user_id", user_m2m="user_ids"),
            dict(name="Recruitment Applicants", model="hr.applicant",
                 title="name", start=["activity_date_deadline","date_open","create_date"], stop=[],
                 user_m2o="user_id", user_m2m=None),
            dict(name="Maintenance Requests", model="maintenance.request",
                 title="name", start=["schedule_date"], stop=[],
                 user_m2o="user_id", user_m2m=None),
            dict(name="Employees (birthdays/expiry)", model="hr.employee",
                 title="name", start=["birthday","visa_expire","id_expiration_date","permit_expiration","expiration_date"], stop=[],
                 user_m2o="user_id", user_m2m=None),
            dict(name="Sales Orders", model="sale.order",
                 title="name", start=["validity_date","commitment_date","date_order"], stop=[],
                 user_m2o="user_id", user_m2m=None),
            dict(name="Purchase Orders", model="purchase.order",
                 title="name", start=["date_order","date_approve"], stop=[],
                 user_m2o="user_id", user_m2m=None),
            dict(name="Meetings (owner)", model="calendar.event",
                 title="name", start=["start"], stop=["stop"],
                 user_m2o="user_id", user_m2m=None),
            dict(
                name="To-Do (Activities)",
                model="project.task",
                title="name",
                start=["date_deadline", "create_date"], stop=[],  # on laissera stop vide; notre duration fallback fera le job si besoin
                user_m2o="user_id", user_m2m=None,
                domain=[("project_id", "=", False)],),

        ]

        for c in requested:
            if not model_exists(c["model"]):
                continue
            mid = self.env['ir.model'].sudo().search([('model', '=', c["model"])], limit=1).id
            exists = self.search([('model_id', '=', mid)], limit=1)
            if exists:
                continue

            vals = {
                "name": c["name"],
                "model_id": mid,
                "title_field_id": field_id(c["model"], c["title"]) or False,
                "start_field_id": first_existing_field_id(c["model"], c["start"]) or False,
                "stop_field_id": first_existing_field_id(c["model"], c["stop"]) or False,
                "user_m2o_field_id": field_id(c["model"], c["user_m2o"]) if c["user_m2o"] else False,
                "user_m2m_field_id": field_id(c["model"], c["user_m2m"]) if c["user_m2m"] else False,
                "visible_to_everyone": False,
            }
            if not vals["start_field_id"]:
                continue
            self.sudo().create(vals)

        action = self.env.ref("global_calendar.action_global_calendar_source").read()[0]
        return action

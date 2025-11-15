# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from datetime import timedelta


_logger = logging.getLogger("GLOBAL_CALENDAR")

def _normalize_hex(h):
    if not h:
        return False
    s = h.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        return False
    try:
        int(s, 16)
    except Exception:
        return False
    return "#" + s.upper()

class GlobalCalendarEvent(models.Model):
    _name = "global.calendar.event"
    _description = "Global Calendar Event"
    _order = "start desc, id desc"

    # --- Champs de base ---
    name = fields.Char("Title", required=True)

    start = fields.Datetime("Start", required=True, index=True)
    stop = fields.Datetime("Stop", index=True)
    all_day = fields.Boolean("All Day")

    # --- Utilisateurs / visibilité ---
    user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="global_calendar_event_users_rel",
        column1="event_id",
        column2="user_id",
        string="Users",
        help="Users concerned by this event.",
    )
    allow_all_users = fields.Boolean(
        string="Visible to everyone",
        help="If enabled, all internal users can see this event.",
        default=False,
    )

    # --- Source ---
    source_id = fields.Many2one("global.calendar.source", string="Source", ondelete="set null")
    model_name = fields.Char("Origin Model", required=True, index=True)
    res_id = fields.Integer("Origin Record ID", required=True, index=True)

    # --- Couleurs ---
    color = fields.Integer(
        "Color (legacy index)",
        compute="_compute_color_index_legacy",
        store=True,
        compute_sudo=True,
    )

    color_hex_effective = fields.Char(
        string="Color HEX",
        compute="_compute_color_hex_effective",
        store=True,
        compute_sudo=True,
    )

    text_color_hex = fields.Char(
        string="Text Color HEX",
        compute="_compute_text_color_hex",
        store=True,
        compute_sudo=True,
    )

    # --- Société ---
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        compute="_compute_company",
        store=True,
        compute_sudo=True,
    )

    # --- User principal (gardé !) ---
    user_id = fields.Many2one(
        "res.users",
        string="User (primary)",
        compute="_compute_user_id",
        store=True,
        compute_sudo=True,
    )

    _sql_constraints = [
        ("global_calendar_event_unique", "unique(model_name, res_id, source_id)",
         "There is already a global calendar event for this record."),
    ]

    # --- Compute methods ---
    @api.depends("user_ids")
    def _compute_company(self):
        for rec in self:
            rec.company_id = rec.user_ids[:1].company_id.id if rec.user_ids else False

    @api.depends('user_ids', 'model_name', 'source_id.color_hex', 'source_id.color_index')
    def _compute_color_index_legacy(self):
        def _fallback_index(rec):
            base = rec.user_ids[:1].id if rec.user_ids else sum(ord(c) for c in (rec.model_name or ''))
            return base % 12
        for rec in self:
            if rec.source_id and rec.source_id.color_index is not None:
                rec.color = rec.source_id.color_index % 12
            else:
                rec.color = _fallback_index(rec)
            # _logger.warning(
            #     "[GLOBAL_CALENDAR][EVENT][COLOR_INDEX] event_id=%s idx=%s",
            #     rec.id or 0, rec.color
            # )

    @api.depends('source_id.color_hex')
    def _compute_color_hex_effective(self):
        for rec in self:
            hx = _normalize_hex(rec.source_id.color_hex if rec.source_id else None) or "#3A53BB"
            rec.color_hex_effective = hx
            # _logger.warning(
            #     "[GLOBAL_CALENDAR][EVENT][COLOR_HEX] event_id=%s hex=%s",
            #     rec.id or 0, hx
            # )

    # @api.depends('color_hex_effective')
    # def _compute_text_color_hex(self):
    #     def _luma(hex6):
    #         s = hex6.lstrip("#")
    #         r = int(s[0:2], 16)
    #         g = int(s[2:4], 16)
    #         b = int(s[4:6], 16)
    #         return 0.2126*r + 0.7152*g + 0.0722*b
    #     for rec in self:
    #         hx = rec.color_hex_effective or "#3A53BB"
    #         rec.text_color_hex = "#000000" if _luma(hx) > 186 else "#FFFFFF"

    @api.depends('color_hex_effective')
    def _compute_text_color_hex(self):
        def _hex_to_rgb01(hex6):
            s = (hex6 or "").lstrip("#")
            if len(s) != 6:
                s = "3A53BB"  # fallback
            r = int(s[0:2], 16) / 255.0
            g = int(s[2:4], 16) / 255.0
            b = int(s[4:6], 16) / 255.0
            return r, g, b

        def _srgb_to_lin(v):
            # Conversion sRGB -> lin (WCAG)
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

        def _relative_luminance(hex6):
            r, g, b = _hex_to_rgb01(hex6)
            R = _srgb_to_lin(r)
            G = _srgb_to_lin(g)
            B = _srgb_to_lin(b)
            return 0.2126 * R + 0.7152 * G + 0.0722 * B

        def _contrast_ratio(L1, L2):
            # L1 >= L2
            return (L1 + 0.05) / (L2 + 0.05)

        for rec in self:
            bg = rec.color_hex_effective or "#3A53BB"
            L_bg = _relative_luminance(bg)
            # Contraste avec blanc (L=1) et noir (L=0)
            contrast_white = _contrast_ratio(1.0, L_bg)
            contrast_black  = _contrast_ratio(max(L_bg, 0.0), 0.0)
            rec.text_color_hex = '#FFFFFF' if contrast_white >= contrast_black else '#000000'



    def _compute_user_id(self):
        for rec in self:
            rec.user_id = rec.user_ids[:1].id if rec.user_ids else False

    # --- Logging hooks ---
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        # _logger.warning(
        #     "[GLOBAL_CALENDAR][EVENT][CREATE] event_id=%s model=%s res=%s title=%s source=%s",
        #     rec.id, rec.model_name, rec.res_id, rec.name,
        #     rec.source_id.id if rec.source_id else None
        # )
        return rec

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            _logger.warning(
                "[GLOBAL_CALENDAR][EVENT][UPDATE] event_id=%s changes=%s now name=%s start=%s stop=%s all_day=%s source=%s hex=%s",
                rec.id, list(vals.keys()), rec.name, rec.start, rec.stop, rec.all_day,
                rec.source_id.id if rec.source_id else None, rec.color_hex_effective
            )
        return res

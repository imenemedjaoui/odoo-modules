from odoo import models, fields, api
from odoo.tools.float_utils import float_is_zero

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    state_custom = fields.Selection([
        ('in_service', 'En Service'),
        ('out_service', 'Hors Service'),
        ('in_repair', 'En Réparation'),
        ('in_inventory', 'En Inventaire')
    ], string="État de l'équipement", default='in_service')

    calibration_date = fields.Date(string="Date de calibration")
    
    recall_date = fields.Date(string="Date de rappel")

    equipment_image = fields.Image(string="Image de l'équipement") 

    # --- Nouveaux champs ---
    # Tracking du produit pour piloter l'affichage du champ lot/numéro de série
    product_tracking = fields.Selection(
        related="product_id.tracking", string="Type de suivi", store=False
    )

    # Lien direct vers le lot/numéro de série
    lot_id = fields.Many2one(
        'stock.lot',
        string="Numéro de série",
        domain="[('product_id','=',product_id), ('company_id','in',[False, company_id]), ('product_qty','>',0)]",
        help="Sélectionne le numéro de série à lier à cet équipement."
    )

    # ---------- Onchanges (UI) ----------
    @api.onchange('product_id')
    def _onchange_product_id_fill_from_product(self):
        """Quand on choisit un produit : reset du lot + pré-remplir modèle & coût."""
        for rec in self:
            if rec.product_id:
                rec.lot_id = False
                rec.model = rec.product_id.default_code or rec.product_id.display_name
                move = self.env['stock.move'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('state', '=', 'done'),
                    ('picking_id.picking_type_code', '=', 'incoming'),
                    ('company_id', '=', (rec.company_id or self.env.company).id),
                    ('purchase_line_id', '!=', False),                          # (optionnel) vient d'un PO
                ], order='date desc, id desc', limit=1)

                # rec.cost = move.price_unit or 0.0
                rec.cost = rec._compute_purchase_unit_price_ttc(move) if move else (rec.product_id.standard_price or 0.0)


    @api.onchange('product_id', 'company_id')
    def _onchange_product_domain_lot(self):
        """Filtre le champ lot_id : uniquement les lots du produit (et de la société)."""
        for rec in self:
            domain = []
            if rec.product_id:
                domain.append(('product_id', '=', rec.product_id.id))
            if rec.company_id:
                domain.append(('company_id', 'in', [False, rec.company_id.id]))
            return {'domain': {'lot_id': domain}}

    @api.onchange('lot_id')
    def _onchange_lot_id_fill_serial(self):
        """Au choix du lot, remplir serial_no pour l'affichage immédiat."""
        for rec in self:
            if rec.lot_id:
                rec.serial_no = rec.lot_id.name
                move = self.env['stock.move'].search([
                    ('product_id', '=', rec.lot_id.product_id.id),
                    ('state', '=', 'done'),
                    ('picking_id.picking_type_code', '=', 'incoming'),
                    ('move_line_ids.lot_id', '=', rec.lot_id.id),
                    ('company_id', '=', (rec.company_id or self.env.company).id),
                    ('purchase_line_id', '!=', False),                          # (optionnel) vient d'un PO
                ], order='date desc, id desc', limit=1)

                # rec.cost = move.price_unit or 0.0
                rec.cost = rec._compute_purchase_unit_price_ttc(move) if move else rec.cost


    # ---------- Complétion server-side SANS boucle ----------
    def _compute_missing_from_product_lot(self, incoming_vals=None):
        """
        Prépare des valeurs à compléter après create/write, sans déclencher de boucles.
        On n'écrit que ce qui manque et seulement si différent.
        """
        updates_per_rec = {}
        incoming_vals = incoming_vals or {}
        for rec in self:
            upd = {}
            # Depuis le lot
            if rec.lot_id and not incoming_vals.get('serial_no') and not rec.serial_no:
                if rec.lot_id.name and rec.serial_no != rec.lot_id.name:
                    upd['serial_no'] = rec.lot_id.name
            # Depuis le produit
            if rec.product_id:
                if not incoming_vals.get('model') and not rec.model:
                    val_model = rec.product_id.default_code or rec.product_id.display_name
                    if val_model and rec.model != val_model:
                        upd['model'] = val_model
                # if not incoming_vals.get('cost') and (not rec.cost or rec.cost == 0.0):
                #     val_cost = rec.product_id.standard_price or 0.0
                #     if rec.cost != val_cost:
                #         upd['cost'] = val_cost
                
                if not incoming_vals.get('cost') and (not rec.cost or float_is_zero(rec.cost, precision_digits=2)):
                    move = self.env['stock.move'].search([
                        ('state', '=', 'done'),
                        ('picking_id.picking_type_code', '=', 'incoming'),
                        ('company_id', '=', (rec.company_id or self.env.company).id),
                        ('purchase_line_id', '!=', False),
                        ('product_id', '=', (rec.lot_id.product_id.id if rec.lot_id else rec.product_id.id)),
                    ] + ([('move_line_ids.lot_id', '=', rec.lot_id.id)] if rec.lot_id else []),
                    order='date desc, id desc', limit=1)
                    val_cost = rec._compute_purchase_unit_price_ttc(move) if move else (rec.product_id.standard_price or 0.0)
                    if not float_is_zero((val_cost or 0.0) - (rec.cost or 0.0), precision_digits=2):
                        upd['cost'] = val_cost

            if upd:
                updates_per_rec[rec.id] = upd
        return updates_per_rec

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Compléter proprement après création (sans relancer la logique)
        for rec, vals in zip(records, vals_list):
            updates = rec._compute_missing_from_product_lot(incoming_vals=vals).get(rec.id)
            if updates:
                super(MaintenanceEquipment, rec.with_context(skip_apply=True)).write(updates)
        return records

    def write(self, vals):
        # Ne pas reboucler si on vient d'un write "silencieux"
        if self.env.context.get('skip_apply'):
            return super().write(vals)

        res = super().write(vals)
        # Compléter après write normal
        for rec in self:
            updates = rec._compute_missing_from_product_lot(incoming_vals=vals).get(rec.id)
            if updates:
                super(MaintenanceEquipment, rec.with_context(skip_apply=True)).write(updates)
        return res

    # ---------- Smart button : ouvrir le lot ----------
    def action_open_lot(self):
        """Ouvre le lot/numéro de série lié en vue formulaire."""
        self.ensure_one()
        if not self.lot_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": self.lot_id.display_name or "Numéro de série",
            "res_model": "stock.lot",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
            "res_id": self.lot_id.id,
            "context": dict(self.env.context, default_product_id=self.product_id.id),
        }
    
    def _compute_purchase_unit_price_ttc(self, move):
        """Prix unitaire TTC (1 pièce) en devise société à partir d'un stock.move d'achat."""
        self.ensure_one()
        pol = move.purchase_line_id
        if not pol:
            return 0.0

        company = (self.company_id or self.env.company)
        order = pol.order_id
        currency = order.currency_id or company.currency_id
        partner = order.partner_id
        product = pol.product_id

        base_price = pol.price_unit * (1 - (pol.discount or 0.0) / 100.0)
        taxes = pol.taxes_id.with_company(company)
        res = taxes.compute_all(
            base_price,
            currency=currency,
            quantity=1.0,
            product=product,
            partner=partner,
            is_refund=False,
            handle_price_include=True,
        )
        unit_ttc_in_order_currency = res['total_included']
        price_company = currency._convert(
            unit_ttc_in_order_currency,
            company.currency_id,
            company,
            order.date_order or fields.Date.today()
        )
        return price_company

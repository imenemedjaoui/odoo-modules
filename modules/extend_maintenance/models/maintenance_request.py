from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    # ⛔️ Ne plus toucher à maintenance_type (on retire le selection_add)
    # maintenance_type = fields.Selection(... selection_add=[('external', ...)])  # <- SUPPRIMER si présent

    # ✅ Nouveau champ pour le mode d'exécution
    maintenance_flow = fields.Selection(
        [('internal', 'Interne'), ('external', 'Externe (Sous-traitance)')],
        string="Exécution",
        default='internal',
        required=True
    )

    # 🔁 is_external calculé depuis maintenance_flow
    is_external = fields.Boolean(
        string="Maintenance externe",
        compute="_compute_is_external",
        store=True
    )

    partner_id = fields.Many2one('res.partner', string="Fournisseur (sous-traitant)", domain=[('supplier_rank', '>', 0)])
    vendor_rma = fields.Char(string="N° RMA fournisseur")
    tracking_ref = fields.Char(string="Référence d’expédition")
    purchase_id = fields.Many2one('purchase.order', string="Bon de commande fournisseur", readonly=True, copy=False)
    external_cost = fields.Monetary(string="Coût externe", currency_field='company_currency_id', readonly=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string="Devise", store=True, readonly=True)
    date_sent_vendor = fields.Datetime(string="Envoyé chez fournisseur")
    date_back_vendor = fields.Datetime(string="Reçu du fournisseur")

    @api.depends('maintenance_flow')
    def _compute_is_external(self):
        for r in self:
            r.is_external = (r.maintenance_flow == 'external')

    # ---------- Helpers ----------
    def _get_or_create_external_service_product(self):
        """Produit service générique pour la ligne de commande fournisseur."""
        Product = self.env['product.product']
        product = Product.search([('default_code', '=', 'EXT_MAINT'), ('type', '=', 'service')], limit=1)
        if not product:
            product = Product.create({
                'name': 'Maintenance externe',
                'default_code': 'EXT_MAINT',
                'type': 'service',
                'purchase_ok': True,
                'sale_ok': False,
            })
        return product

    # ---------- Actions ----------
    def action_create_vendor_rfq(self):
        """Créer un devis fournisseur et le lier au ticket."""
        self.ensure_one()
        if not self.is_external:
            raise UserError(_("Le ticket n'est pas marqué comme maintenance externe."))
        if not self.partner_id:
            raise UserError(_("Veuillez choisir un fournisseur."))

        product = self._get_or_create_external_service_product()

        # Description riche pour le fournisseur
        equip = self.equipment_id
        sn = equip.serial_no or getattr(equip, 'lot_id', False) and equip.lot_id.name or ''
        desc = _(
            "Maintenance externe pour l'équipement: %(eq)s\n"
            "- Numéro de série: %(sn)s\n"
            "- Catégorie: %(cat)s\n"
            "- Problème: %(p)s\n"
            "- Ticket: %(tname)s (%(tid)s)"
        ) % {
            'eq': equip.display_name or '',
            'sn': sn or '-',
            'cat': equip.category_id.display_name or '',
            'p': self.name or self.description or '',
            'tname': self.name,
            'tid': self.id,
        }

        PO = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'origin': f"MR{self.id} - {self.name}",
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': desc,
                'product_qty': 1.0,
                'price_unit': 0.0,
                'product_uom': product.uom_id.id,
                'date_planned': fields.Datetime.now(),
            })],
        })
        self.write({
            'purchase_id': PO.id,
            'date_sent_vendor': fields.Datetime.now(),
        })

        # Option : activité pour penser à confirmer/valider le PO
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=_("Traiter le devis fournisseur"),
            note=_("Vérifier le devis créé et le confirmer si OK."),
            user_id=self.env.user.id,
            date_deadline=fields.Date.today(),
        )

        # Passer l'étape du ticket si tu utilises des étapes personnalisées
        if hasattr(self, 'stage_id'):
            stage = self.env['maintenance.stage'].search([('name', 'ilike', 'Chez fournisseur')], limit=1)
            if stage:
                self.stage_id = stage.id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': PO.id,
            'target': 'current',
        }

    def action_mark_back_from_vendor(self):
        """Marquer l'équipement comme revenu du fournisseur et remonter le coût depuis le PO."""
        self.ensure_one()
        updates = {'date_back_vendor': fields.Datetime.now()}
        if self.purchase_id:
            # On prend le total TTC du PO comme coût externe (adapte si tu veux le HT)
            updates['external_cost'] = self.purchase_id.amount_total
        self.write(updates)

        # Étape retour (si tu as la colonne stage)
        if hasattr(self, 'stage_id'):
            stage = self.env['maintenance.stage'].search([('name', 'ilike', 'Reçu du fournisseur')], limit=1)
            if stage:
                self.stage_id = stage.id

        return True
    
    def action_open_purchase(self):
        self.ensure_one()
        if not self.purchase_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": self.purchase_id.display_name or "Bon de commande",
            "res_model": "purchase.order",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
            "res_id": self.purchase_id.id,
        }


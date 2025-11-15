from odoo import models, api

class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def create(self, vals):
        # Force suppression automatique à False
        vals['auto_delete'] = False

        # Forcer l'utilisation du serveur SMTP configuré
        smtp_server = self.env['ir.mail_server'].search([], limit=1)
        if smtp_server:
            vals['mail_server_id'] = smtp_server.id

        return super(MailMail, self).create(vals)
    
    def write(self, vals):
        # Si l'objet est modifié ultérieurement, on force à nouveau les valeurs
        vals.setdefault('auto_delete', False)

        smtp_server = self.env['ir.mail_server'].search([], limit=1)
        if smtp_server:
            vals.setdefault('mail_server_id', smtp_server.id)

        return super(MailMail, self).write(vals)

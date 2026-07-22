/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Component, onMounted, onWillUnmount, useState } from '@odoo/owl';
import { useService } from '@web/core/utils/hooks';
import { standardFieldProps } from '@web/views/fields/standard_field_props';

/**
 * Widget invisible qui fait le polling et rafraîchit automatiquement la vue
 */
export class TaskTimerPoller extends Component {
    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService('notification');
        this.timerId = null;
        this.limitNotified = false;
        
        this.state = useState({
            timerDisplay: '',
            timerRunning: false,
            timerPaused: false,
        });

        onMounted(() => {
            this._startPolling();
        });

        onWillUnmount(() => {
            this._stopPolling();
        });
    }

    _startPolling() {
        if (this.timerId) {
            return;
        }

        // Premier refresh immédiat
        this._refreshTimer();

        // Polling toutes les secondes
        this.timerId = setInterval(() => {
            this._refreshTimer();
        }, 1000);
    }

    async _refreshTimer() {
        const record = this.props.record;

        if (!record || !record.resId) {
            return;
        }

        const taskId = record.resId;

        try {
            // Appel RPC pour forcer le compute côté serveur
            const timerInfo = await this.orm.call('project.task', 'get_timer_info', [taskId]);

            if (!timerInfo) {
                return;
            }

            // Mettre à jour l'état local pour forcer le re-render
            this.state.timerDisplay = timerInfo.display;
            this.state.timerRunning = timerInfo.allocated_limit_reached ? false : record.data.timer_running;
            this.state.timerPaused = record.data.timer_paused;

            // Mettre à jour le record
            if (record.data) {
                record.data.timer_display = timerInfo.display;
                record.data.timer_color = timerInfo.color;
                
                // Forcer la mise à jour visuelle en déclenchant un changement
                record.model.root.data.timer_display = timerInfo.display;
            }

            // Vérifier si la limite vient d'être atteinte
            if (timerInfo.limit_reached && !this.limitNotified) {
                this.limitNotified = true;
                
                // NOTIFICATION CRITIQUE
                this.notification.add(
                    "⏰ Le chronomètre a atteint la limite des heures allouées et a été mis en pause automatiquement !",
                    {
                        title: "⚠️ Limite d'heures atteinte",
                        type: 'warning',
                        sticky: true,
                    }
                );

                // Ouvrir le wizard
                setTimeout(async () => {
                    await this.action.doAction({
                        type: 'ir.actions.act_window',
                        res_model: 'project.task.timer.wizard',
                        name: 'Enregistrer le temps - Limite atteinte',
                        views: [[false, 'form']],
                        target: 'new',
                        context: {
                            default_task_id: taskId,
                            default_name: '',
                            default_time_spent: record.data.timer_spent_total || 0,
                        },
                    });
                }, 500);
            }
            
            // Réinitialiser le flag si la limite n'est plus atteinte
            if (!timerInfo.limit_reached && this.limitNotified) {
                this.limitNotified = false;
            }

            // Forcer le rafraîchissement complet de la vue
            if (record.model && typeof record.model.load === 'function') {
                await record.model.load();
            }
            
            // Trigger render pour toutes les vues
            if (this.env && this.env.bus) {
                this.env.bus.trigger('RELATIONAL_MODEL:NEED_LOCAL_CHANGES', { 
                    resModel: 'project.task',
                    resId: taskId 
                });
            }

        } catch (error) {
            console.error('Erreur lors du polling du timer :', error);
        }
    }

    _stopPolling() {
        if (this.timerId) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
    }
}

TaskTimerPoller.template = 'project_task_timer_custom.TaskTimerPoller';

TaskTimerPoller.props = {
    ...standardFieldProps,
};

export const taskTimerPollerField = {
    component: TaskTimerPoller,
};

registry.category('fields').add('task_timer_poller', taskTimerPollerField);

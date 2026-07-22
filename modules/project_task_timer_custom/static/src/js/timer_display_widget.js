/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Component, onMounted, onWillUnmount, useState } from '@odoo/owl';
import { useService } from '@web/core/utils/hooks';
import { standardFieldProps } from '@web/views/fields/standard_field_props';

/**
 * Widget pour afficher le timer en temps réel avec auto-refresh
 */
export class TimerDisplayWidget extends Component {
    setup() {
        this.orm = useService('orm');
        this.notification = useService('notification');
        this.action = useService('action');
        this.timerId = null;
        this.limitNotified = false;
        
        this.state = useState({
            display: '00:00:00',
            color: 'black',
        });

        onMounted(() => {
            // Initialiser l'affichage
            const initialValue = this.props.record?.data?.timer_display;
            if (initialValue) {
                this.state.display = initialValue;
            }
            this._startTimer();
        });

        onWillUnmount(() => {
            this._stopTimer();
        });
    }

    _startTimer() {
        if (this.timerId) return;
        
        this.timerId = setInterval(async () => {
            await this._updateDisplay();
        }, 1000);
    }

    async _updateDisplay() {
        const record = this.props.record;
        if (!record || !record.resId) return;

        try {
            const timerInfo = await this.orm.call(
                'project.task',
                'get_timer_info',
                [record.resId]
            );

            if (timerInfo) {
                this.state.display = timerInfo.display;
                this.state.color = timerInfo.color;

                // Mettre à jour le record
                if (record.data && record.data.timer_display !== undefined) {
                    record.data.timer_display = timerInfo.display;
                }

                // Vérifier si limite atteinte pour notification
                if (timerInfo.limit_reached && !this.limitNotified) {
                    this.limitNotified = true;
                    
                    this.notification.add(
                        "⏰ Le chronomètre a atteint la limite des heures allouées et a été mis en pause automatiquement !",
                        {
                            title: "⚠️ Limite d'heures atteinte",
                            type: 'warning',
                            sticky: true,
                        }
                    );

                    // Ouvrir le wizard après un court délai
                    setTimeout(async () => {
                        const task = await this.orm.read('project.task', [record.resId], ['name', 'timer_spent_total']);
                        if (task && task.length > 0) {
                            await this.action.doAction({
                                type: 'ir.actions.act_window',
                                res_model: 'project.task.timer.wizard',
                                name: 'Enregistrer le temps - Limite atteinte',
                                views: [[false, 'form']],
                                target: 'new',
                                context: {
                                    default_task_id: record.resId,
                                    default_name: task[0].name || 'Travail sur la tâche',
                                    default_time_spent: task[0].timer_spent_total || 0,
                                },
                            });
                        }
                    }, 500);
                }
                
                if (!timerInfo.limit_reached) {
                    this.limitNotified = false;
                }
            }
        } catch (error) {
            console.error('Erreur update timer:', error);
        }
    }

    _stopTimer() {
        if (this.timerId) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
    }

    get displayStyle() {
        return `color: ${this.state.color}; font-weight: bold; font-size: 16px;`;
    }
}

TimerDisplayWidget.template = 'project_task_timer_custom.TimerDisplayWidget';

TimerDisplayWidget.props = {
    ...standardFieldProps,
};

TimerDisplayWidget.supportedTypes = ["char"];

export const timerDisplayLiveField = {
    component: TimerDisplayWidget,
};

registry.category('fields').add('timer_display_live', timerDisplayLiveField);

from celery import shared_task


# Django -> Celery Task -> Redis -> Celery Worker -> EfficientNetB0 Training -> Model Artifact -> PostgreSQL Metadata.

# The HTTP request that queues this (training.api_views.train_api) returns immediately with this task's id; it never runs training
# inline. All actual work — and all TrainingJob/ModelVersion/AuditLog writes — happens in training.ml_pipeline.train_efficientnet, which
# this task simply invokes on the worker.
@shared_task(bind=True, name='training.train_model_task')
def train_model_task(self, training_job_id):
    from .models import TrainingJob

    # Record the real Celery task id against the job row (the one handed back to the caller at queue time is a client-side placeholder from
    # .delay(); this is belt-and-suspenders in case they ever diverge).
    TrainingJob.objects.filter(pk=training_job_id).update(task_id=self.request.id)

    from .ml_pipeline import train_efficientnet
    return train_efficientnet(training_job_id)
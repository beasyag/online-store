from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_order_payment_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="stripe_checkout_session_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="order",
            name="stripe_payment_intent_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]

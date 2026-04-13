from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("cash_on_delivery", "Cash on delivery"),
                    ("card_on_delivery", "Card on delivery"),
                    ("card_online", "Card online"),
                ],
                default="card_on_delivery",
                max_length=30,
            ),
        ),
    ]

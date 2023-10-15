from worker import celery
from flask import current_app as app
from models import USER,Theatre,Show,Ticket
from mail import send_email
from jinja2 import Template
from sqlalchemy import not_
from celery import Celery
from celery.schedules import crontab
from dataclasses import asdict

@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(crontab(hour=21, minute=00), daily_reminder.s(), name='everyday 9PM')
    sender.add_periodic_task(600.0, monthly_reminder.s(), name='everyday month')

    # Calls test('world') every 30 seconds
    #sender.add_periodic_task(30.0, test.s('world'), expires=10)

    # Executes every Monday morning at 7:30 a.m.
    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     test.s('Happy Mondays!'),
    # )

@celery.task()
def just_say_hello():
    print("HEHEHEHHEHE")

@celery.task()
def daily_reminder():
    users = USER.query.all()
    for user in users:
        bookings = Ticket.query.filter_by(user_id=user.user_id).all()
        result = []
        for booking in bookings:
            show = Show.query.filter(not_(Show.show_id == booking.show_id)).first()
            if show:
                result.append({
                    'show_id': show.show_id,
                    'name': show.name,
                    'rating': show.rating
                })
        with open("project/public/mail.html", "r") as b:
            html = Template(b.read())
            send_email(user.username, subject="daily reminder", message=html.render(user=user, result=result))

@celery.task()
def monthly_reminder():
    users = USER.query.all()
    for user in users:

        bookings = Ticket.query.filter_by(user_id=user.user_id).all()
        show_details = []
        for booking in bookings:
            show = Show.query.get(booking.show_id)
            if show:
                theatre = Theatre.query.filter(Theatre.theatre_id==show.theatre_id).first()
                show_dict = show.__dict__
                show_dict["booked_tickets"] = booking.booked_tickets
                show_dict["theatre_name"] = theatre.name
                show_details.append(show_dict)
        with open("project/public/monthly.html","r") as b:
            html=Template(b.read())
            send_email(user.username, subject="monthly progress", message=html.render(user=user,show_details=show_details))

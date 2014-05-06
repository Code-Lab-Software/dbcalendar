# -*- coding: utf-8 -*-
import datetime

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models import get_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from dormitorysetup.base import PublicationTracker, ChoiceBase
from dormitorysetup.models import Room

#--------------------------------------------------------------------------------
# Modele zwiazne z kalendarzem ogolnym
#--------------------------------------------------------------------------------

class CalendarYear(PublicationTracker):
    '''Model reprezenrujacy jeden rok kalendzarzowy w systemie '''
    name = models.SlugField(verbose_name=u"Calendar year code name", unique=True)
    year_number = models.PositiveIntegerField(verbose_name=u"Calendar year number", unique=True )

    def __unicode__(self):
        return u"%s" % self.year_number

    def clean(self):
        if self.year_number < datetime.datetime.now().year:
            raise ValidationError( u"Can't add historical years")

    class Meta:
        verbose_name = u"Calendar year"
        verbose_name_plural = u"Calendar years"


class CalendarMonthName(ChoiceBase):
    JANUARY = (1, 'January')
    FEBRUARY = (2, 'February')
    MARCH = (3, 'March')
    APRIL = (4, 'April')
    MAY = (5, 'May')
    JUNE = (6, 'June')
    JULY = (7, 'July')
    AUGUST = (8, 'August')
    SEPTEMBER = (9, 'September')
    OCTOBER = (10, 'October')
    NOVEMBER = (11, 'November')
    DECEMBER = (12, 'December')


class CalendarMonth(PublicationTracker):
    '''Model reprezentujacy miesiące przynalezne do danego roku kalendarzowego.'''

    calendar_year = models.ForeignKey('CalendarYear', verbose_name=u"Calendar year", related_name="calendarmonths")
    month_number = models.PositiveIntegerField(verbose_name=u"Month number", choices=CalendarMonthName)

    def __unicode__(self):
        return u"%s (%s)" % (self.month_number, self.calendar_year)

    class Meta:
        unique_together = ( ('calendar_year', 'month_number'),)
        verbose_name = u"Calendar month"
        verbose_name_plural = u"Calendar months"


class CalendarWeek(PublicationTracker):
    '''Model reprezentujacy tygodnie przynalezne do danego roku kalendarzowego.
       Tygodnie tworza sie automatycznie po dodaniu roku na sygnale post_save'''

    calendar_year = models.ForeignKey('CalendarYear', verbose_name=u"Calendar year", related_name="calendarweeks")
    week_number = models.PositiveIntegerField(verbose_name=u"Week number")

    def __unicode__(self):
        return u"%s (%s)" % (self.week_number, self.calendar_year)

    def clean(self):
        #pierwsze dni nowego roku moga miec zerowy numer tydgodnia ze wzgledu na kalendarz ISO
        if week_number < 0 or week_number > 54:
            raise ValidationError(u"Wrong week number! Schould be in [0, 54]")

    class Meta:
        unique_together = ( ('calendar_year', 'week_number'),)
        verbose_name = u"Calendar week"
        verbose_name_plural = u"Calendar weeks"


class CalendarDayName(ChoiceBase):
    MONDAY = (1, 'Monday')
    TUESDAY = (2, 'Tuesday')
    WEDNESDAY = (3, 'Wednesday')
    THURSDAY = (4, 'Thuersday')
    FRIDAY = (5, 'Friday')
    SATURDAY = (6, 'Saturday')
    SUNDAY = (7, 'Sunday')


class CalendarDay(PublicationTracker):
    '''Model reprezentujacy jeden dzien. Obiekty tworza sie automatycznie po dodaniu roku '''
    calendar_week = models.ForeignKey('CalendarWeek', verbose_name=u"Calendar week", related_name='calendardays')
    calendar_month = models.ForeignKey('CalendarMonth', verbose_name=u"Calendar month", related_name='calendardays')
    week_day_number = models.PositiveIntegerField(choices=CalendarDayName, verbose_name=u"Week day number")
    date = models.DateField(verbose_name="Date")

    def __unicode__(self):
        return u"%s %s (week=%s)" % (self.date, self.get_week_day_number_display(),  self.calendar_week)

    def get_week_day_number_display(self):
        return CalendarDayName._get_value(self.week_day_number)

    class Meta:
        unique_together = ( ('calendar_week','date'), ('calendar_week', 'week_day_number'),)
        verbose_name = u"Calendar day"
        verbose_name_plural = u"Calendar days"


#Autmatyczne tworzenie obiektow week, month i day po dodaniu obiektu year
@receiver(post_save, sender=CalendarYear)
def create_day_and_week(sender, instance, created, **kwargs):
    if created:
        #zlicz ilosc tygodni
        #klendarz ISO ostani tydzien grudnia moze zliczyc jako pierwszy nowego roku
        last_week = 1
        end_day = 31
        year = instance.year_number

        while last_week == 1:
            last_week = datetime.date(year, 12, end_day).isocalendar()[1];
            end_day = end_day - 1

        if end_day == 30:
            last_week = last_week
        else:
            last_week = last_week + 1

        #lecimy ze wszystkimi dniami i miesiacami i twrzymy odpowiednie wpisy
        for month in xrange(1, 13):
            calendar_month, created_month_obj = CalendarMonth.objects.get_or_create(calendar_year=instance, month_number=month)
            for day in xrange(1,32):
                try:
                    cal_date = datetime.date(year, month, day)
                    iso_cal = cal_date.isocalendar()
                    actual_week = iso_cal[1]
                    actual_day = iso_cal[2]
                    #uwaga na zmane pierwszego tygodnia w kalendarzu ISO
                    if month == 1 and iso_cal[0] == year-1:
                        actual_week = 0
                    #uwaga na zmane ostatniego tygodnia w kalendarzu ISO
                    if month == 12 and  actual_week == 1:
                        actual_week = last_week

                    week, created_obj = CalendarWeek.objects.get_or_create(calendar_year=instance, week_number=actual_week)
                    CalendarDay.objects.get_or_create(calendar_week=week, calendar_month=calendar_month, week_day_number=actual_day, date=cal_date)

                except ValueError:
                    break

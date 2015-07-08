import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.contrib.staticfiles.templatetags.staticfiles import static

from timezone_field import TimeZoneField


# Bestiary database models
class Monster(models.Model):
    ELEMENT_FIRE = 'fire'
    ELEMENT_WIND = 'wind'
    ELEMENT_WATER = 'water'
    ELEMENT_LIGHT = 'light'
    ELEMENT_DARK = 'dark'

    TYPE_ATTACK = 'attack'
    TYPE_HP = 'hp'
    TYPE_SUPPORT = 'support'
    TYPE_DEFENSE = 'defense'
    TYPE_MATERIAL = 'material'

    ELEMENT_CHOICES = (
        (ELEMENT_FIRE, 'Fire'),
        (ELEMENT_WIND, 'Wind'),
        (ELEMENT_WATER, 'Water'),
        (ELEMENT_LIGHT, 'Light'),
        (ELEMENT_DARK, 'Dark'),
    )

    TYPE_CHOICES = (
        (TYPE_ATTACK, 'Attack'),
        (TYPE_HP, 'HP'),
        (TYPE_SUPPORT, 'Support'),
        (TYPE_DEFENSE, 'Defense'),
        (TYPE_MATERIAL, 'Material'),
    )

    STAR_CHOICES = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
        (6, 6),
    )

    name = models.CharField(max_length=40)
    image_filename = models.CharField(max_length=250, null=True, blank=True)
    element = models.CharField(max_length=6, choices=ELEMENT_CHOICES, default=ELEMENT_FIRE)
    archetype = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_ATTACK)
    base_stars = models.IntegerField(choices=STAR_CHOICES)
    can_awaken = models.BooleanField(default=True)
    is_awakened = models.BooleanField(default=False)
    skills = models.ManyToManyField('MonsterSkill', blank=True)
    base_hp = models.IntegerField(null=True, blank=True)
    base_attack = models.IntegerField(null=True, blank=True)
    base_defense = models.IntegerField(null=True, blank=True)
    base_speed = models.IntegerField(null=True, blank=True)
    base_crit_rate = models.IntegerField(null=True, blank=True)
    base_crit_damage = models.IntegerField(null=True, blank=True)
    base_resistance = models.IntegerField(null=True, blank=True)
    base_accuracy = models.IntegerField(null=True, blank=True)
    awakens_from = models.ForeignKey('self', null=True, blank=True, related_name='+')
    awakens_to = models.ForeignKey('self', null=True, blank=True, related_name='+')
    awaken_ele_mats_low = models.IntegerField(null=True, blank=True)
    awaken_ele_mats_mid = models.IntegerField(null=True, blank=True)
    awaken_ele_mats_high = models.IntegerField(null=True, blank=True)
    awaken_magic_mats_low = models.IntegerField(null=True, blank=True)
    awaken_magic_mats_mid = models.IntegerField(null=True, blank=True)
    awaken_magic_mats_high = models.IntegerField(null=True, blank=True)
    fusion_food = models.BooleanField(default=False)

    def image_url(self):
        if self.image_filename:
            return mark_safe('<img src="%s" height="42" width="42"/>' % static('herders/images/monsters/' + self.image_filename))
        else:
            return 'No Image'

    def get_stats(self, grade, level):
        # Check that base stats exist first
        if not self.base_hp or not self.base_attack or not self.base_defense:
            return {
                'hp': -1,
                'atk': -1,
                'def': -1,
            }

        max_lvl = 10 + grade * 5

        # Awakened monster base grade is considered as 1 higher than unawakened base grade from here
        if self.is_awakened:
            stat_base_grade = self.base_stars + 1
        else:
            stat_base_grade = self.base_stars

        weight = float(self.base_hp / 15 + self.base_attack + self.base_defense)
        hp_base = round((self.base_hp / 15 * (105 + (15 * stat_base_grade))) / weight, 0)
        atk_base = round((self.base_attack * (105 + (15 * stat_base_grade))) / weight, 0)
        def_base = round((self.base_defense * (105 + (15 * stat_base_grade))) / weight, 0)

        print 'weight: ' + str(weight)
        print 'hp_base: ' + str(hp_base)
        print 'atk_base: ' + str(atk_base)
        print 'def_base: ' + str(def_base)

        magic_multipliers = [
            {'1': 1.0, 'max': 1.9958},
            {'1': 1.5966, 'max': 3.03050646},
            {'1': 2.4242774, 'max': 4.364426603},
            {'1': 3.4914444, 'max': 5.941390935},
            {'1': 4.7529032, 'max': 8.072330795},
            {'1': 6.4582449, 'max': 10.97901633},
        ]

        hp_lvl_1 = 15 * round(hp_base * magic_multipliers[grade - 1]['1'], 0)
        hp_lvl_max = 15 * round(hp_base * magic_multipliers[grade - 1]['max'], 0)
        atk_lvl_1 = round(atk_base * magic_multipliers[grade - 1]['1'], 0)
        atk_lvl_max = round(atk_base * magic_multipliers[grade - 1]['max'], 0)
        def_lvl_1 = round(def_base * magic_multipliers[grade - 1]['1'], 0)
        def_lvl_max = round(def_base * magic_multipliers[grade - 1]['max'], 0)

        if level == 1:
            actual_hp = hp_lvl_1
            actual_atk = atk_lvl_1
            actual_def = def_lvl_1
        elif level == max_lvl:
            actual_hp = hp_lvl_max
            actual_atk = atk_lvl_max
            actual_def = def_lvl_max
        else:
            # Use exponential function in format value=ae^(bx)
            # a=stat_lvl_1*e^(-b)
            from math import log, exp
            hp_b_coeff = log(hp_lvl_max / hp_lvl_1) / (max_lvl - 1)
            atk_b_coeff = log(atk_lvl_max / atk_lvl_1) / (max_lvl - 1)
            def_b_coeff = log(def_lvl_max / def_lvl_1) / (max_lvl - 1)

            actual_hp = round((hp_lvl_1 * exp(-hp_b_coeff)) * exp(hp_b_coeff * level) / 15, 0) * 15
            actual_atk = round((atk_lvl_1 * exp(-atk_b_coeff)) * exp(atk_b_coeff * level), 0)
            actual_def = round((def_lvl_1 * exp(-def_b_coeff)) * exp(def_b_coeff * level), 0)

        return {
            'hp': actual_hp,
            'atk': actual_atk,
            'def': actual_def,
        }

    def save(self, *args, **kwargs):
        # Update image filename on save.
        if self.is_awakened and self.awakens_from is not None:
            self.image_filename = self.awakens_from.image_filename.replace('.png', '_awakened.png')
        else:
            self.image_filename = self.name.lower().replace(' ', '_') + '_' + str(self.element) + '.png'

        super(Monster, self).save(*args, **kwargs)

    class Meta:
        ordering = ['name', 'element']

    def __unicode__(self):
        if self.is_awakened:
            return self.name
        else:
            return self.name + ' (' + self.element.capitalize() + ')'


class MonsterSkill(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField()
    slot = models.IntegerField(default=1)
    skill_effect = models.ManyToManyField('MonsterSkillEffect', blank=True)
    general_leader = models.BooleanField(default=False)
    dungeon_leader = models.BooleanField(default=False)
    arena_leader = models.BooleanField(default=False)
    guild_leader = models.BooleanField(default=False)
    passive = models.BooleanField(default=False)
    max_level = models.IntegerField()
    level_progress_description = models.TextField(null=True, blank=True)
    icon_filename = models.CharField(max_length=100, null=True, blank=True)

    def image_url(self):
        if self.icon_filename:
            return mark_safe('<img src="%s" height="42" width="42"/>' % static('herders/images/skills/' + self.icon_filename))
        else:
            return 'No Image'

    def __unicode__(self):
        return self.name


class MonsterSkillEffect(models.Model):
    is_buff = models.BooleanField(default=True)
    name = models.CharField(max_length=40)
    description = models.TextField()
    icon_filename = models.CharField(max_length=100, null=True, blank=True)

    def image_url(self):
        if self.icon_filename:
            return mark_safe('<img src="%s" height="42" width="42"/>' % static('herders/images/buffs/' + self.icon_filename))
        else:
            return 'No Image'

    def __unicode__(self):
        return self.name


class Fusion(models.Model):
    product = models.ForeignKey('Monster', related_name='product')
    stars = models.IntegerField()
    cost = models.IntegerField()
    ingredients = models.ManyToManyField('Monster')

    def __unicode__(self):
        return str(self.product) + ' Fusion'


# Individual user/monster collection models
class Summoner(models.Model):
    user = models.OneToOneField(User)
    summoner_name = models.CharField(max_length=256, null=True, blank=True)
    global_server = models.NullBooleanField(default=True, null=True, blank=True)
    public = models.BooleanField(default=False, blank=True)
    timezone = TimeZoneField(default='America/Los_Angeles')
    notes = models.TextField(null=True, blank=True)
    storage_magic_low = models.IntegerField(default=0)
    storage_magic_mid = models.IntegerField(default=0)
    storage_magic_high = models.IntegerField(default=0)
    storage_fire_low = models.IntegerField(default=0)
    storage_fire_mid = models.IntegerField(default=0)
    storage_fire_high = models.IntegerField(default=0)
    storage_water_low = models.IntegerField(default=0)
    storage_water_mid = models.IntegerField(default=0)
    storage_water_high = models.IntegerField(default=0)
    storage_wind_low = models.IntegerField(default=0)
    storage_wind_mid = models.IntegerField(default=0)
    storage_wind_high = models.IntegerField(default=0)
    storage_light_low = models.IntegerField(default=0)
    storage_light_mid = models.IntegerField(default=0)
    storage_light_high = models.IntegerField(default=0)
    storage_dark_low = models.IntegerField(default=0)
    storage_dark_mid = models.IntegerField(default=0)
    storage_dark_high = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        # Bounds checks on essences
        if self.storage_magic_low < 0:
            self.storage_magic_low = 0
        if self.storage_magic_mid < 0:
            self.storage_magic_mid = 0
        if self.storage_magic_high < 0:
            self.storage_magic_high = 0

        if self.storage_fire_low < 0:
            self.storage_fire_low = 0
        if self.storage_fire_mid < 0:
            self.storage_fire_mid = 0
        if self.storage_fire_high < 0:
            self.storage_fire_high = 0

        if self.storage_wind_low < 0:
            self.storage_wind_low = 0
        if self.storage_wind_mid < 0:
            self.storage_wind_mid = 0
        if self.storage_wind_high < 0:
            self.storage_wind_high = 0

        if self.storage_water_low < 0:
            self.storage_water_low = 0
        if self.storage_water_mid < 0:
            self.storage_water_mid = 0
        if self.storage_water_high < 0:
            self.storage_water_high = 0

        if self.storage_dark_low < 0:
            self.storage_dark_low = 0
        if self.storage_dark_mid < 0:
            self.storage_dark_mid = 0
        if self.storage_dark_high < 0:
            self.storage_dark_high = 0

        if self.storage_light_low < 0:
            self.storage_light_low = 0
        if self.storage_light_mid < 0:
            self.storage_light_mid = 0
        if self.storage_light_high < 0:
            self.storage_light_high = 0

        super(Summoner, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s" % self.user


class MonsterInstance(models.Model):
    PRIORITY_DONE = 0
    PRIORITY_LOW = 1
    PRIORITY_MED = 2
    PRIORITY_HIGH = 3

    PRIORITY_CHOICES = (
        (PRIORITY_DONE, 'Done'),
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MED, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey('Summoner')
    monster = models.ForeignKey('Monster')
    stars = models.IntegerField()
    level = models.IntegerField()
    skill_1_level = models.IntegerField(null=True, blank=True)
    skill_2_level = models.IntegerField(null=True, blank=True)
    skill_3_level = models.IntegerField(null=True, blank=True)
    skill_4_level = models.IntegerField(null=True, blank=True)
    fodder = models.BooleanField(default=False)
    in_storage = models.BooleanField(default=False)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=PRIORITY_MED)
    notes = models.TextField(null=True, blank=True)

    def max_level_from_stars(self):
        return 10 + self.stars * 5

    def is_max_level(self):
        return self.level == self.max_level_from_stars()

    def get_stats(self):
        return self.monster.get_stats(self.stars, self.level)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.level > 40 or self.level < 1:
            raise ValidationError(
                'Level out of range (Valid range %(min)s-%(max)s)',
                params={'min': 1, 'max': 40},
                code='invalid_level'
            )

        if self.level > 10 + self.stars * 5:
            raise ValidationError(
                'Level exceeds max for given star rating (Max: %(value)s)',
                params={'value': self.max_level_from_stars()},
                code='invalid_level'
            )

        if self.stars > 6 or self.stars < 1:
            raise ValidationError(
                'Star rating out of range',
                code='invalid_stars'
            )
        super(MonsterInstance, self).clean()

    def __unicode__(self):
        return str(self.monster) + ', ' + str(self.stars) + '*, Lvl ' + str(self.level)

    class Meta:
        ordering = ['-stars', '-level', '-priority', 'monster__name']


class RuneInstance(models.Model):
    TYPE_ENERGY = 1
    TYPE_FATAL = 2
    TYPE_BLADE = 3
    TYPE_RAGE = 4
    TYPE_SWIFT = 5
    TYPE_FOCUS = 6
    TYPE_GUARD = 7
    TYPE_ENDURE = 8
    TYPE_VIOLENT = 9
    TYPE_WILL = 10
    TYPE_NEMESIS = 11
    TYPE_SHIELD = 12
    TYPE_REVENGE = 13
    TYPE_DESPAIR = 14
    TYPE_VAMPIRE = 15

    TYPE_CHOICES = (
        (TYPE_ENERGY, 'Energy'),
        (TYPE_FATAL, 'Fatal'),
        (TYPE_BLADE, 'Blade'),
        (TYPE_RAGE, 'Rage'),
        (TYPE_SWIFT, 'Swift'),
        (TYPE_FOCUS, 'Focus'),
        (TYPE_GUARD, 'Guard'),
        (TYPE_ENDURE, 'Endure'),
        (TYPE_VIOLENT, 'Violent'),
        (TYPE_WILL, 'Will'),
        (TYPE_NEMESIS, 'Nemesis'),
        (TYPE_SHIELD, 'Shield'),
        (TYPE_REVENGE, 'Revenge'),
        (TYPE_DESPAIR, 'Despair'),
        (TYPE_VAMPIRE, 'Vampire'),
    )

    STAT_HP = 1
    STAT_HP_PCT = 2
    STAT_ATK = 3
    STAT_ATK_PCT = 4
    STAT_DEF = 5
    STAT_DEF_PCT = 6
    STAT_SPD = 7
    STAT_CRIT_RATE_PCT = 8
    STAT_CRIT_DMG_PCT = 9
    STAT_RESIST_PCT = 10
    STAT_ACCURACY_PCT = 11

    INNATE_STAT_CHOICES = (
        (STAT_HP, 'HP'),
        (STAT_HP_PCT, 'HP %'),
        (STAT_ATK, 'ATK'),
        (STAT_ATK_PCT, 'ATK %'),
        (STAT_DEF, 'DEF'),
        (STAT_DEF_PCT, 'DEF %'),
        (STAT_SPD, 'SPD'),
        (STAT_CRIT_RATE_PCT, 'CRI Rate %'),
        (STAT_CRIT_DMG_PCT, 'CRI Dmg %'),
        (STAT_RESIST_PCT, 'Resistance %'),
        (STAT_ACCURACY_PCT, 'Accuracy %'),
    )

    STAT_CHOICES = (
        (STAT_HP, 'HP'),
        (STAT_HP_PCT, 'HP %'),
        (STAT_ATK, 'ATK'),
        (STAT_ATK_PCT, 'ATK %'),
        (STAT_DEF, 'DEF'),
        (STAT_DEF_PCT, 'DEF %'),
        (STAT_SPD, 'SPD'),
        (STAT_CRIT_RATE_PCT, 'CRI Rate %'),
        (STAT_CRIT_DMG_PCT, 'CRI Dmg %'),
        (STAT_RESIST_PCT, 'Resistance %'),
        (STAT_ACCURACY_PCT, 'Accuracy %'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.IntegerField(choices=TYPE_CHOICES)
    owner = models.ForeignKey(Summoner)
    monster = models.ForeignKey('MonsterInstance', null=True, blank=True)
    stars = models.IntegerField()
    level = models.IntegerField()
    slot = models.IntegerField()
    main_stat = models.IntegerField(choices=STAT_CHOICES)
    main_stat_value = models.IntegerField(default=0)
    innate_stat = models.IntegerField(choices=INNATE_STAT_CHOICES, null=True, blank=True)
    innate_stat_value = models.IntegerField(null=True, blank=True)
    substat_1 = models.IntegerField(choices=STAT_CHOICES, null=True, blank=True)
    substat_1_value = models.IntegerField(null=True, blank=True)
    substat_2 = models.IntegerField(choices=STAT_CHOICES, null=True, blank=True)
    substat_2_value = models.IntegerField(null=True, blank=True)
    substat_3 = models.IntegerField(choices=STAT_CHOICES, null=True, blank=True)
    substat_3_value = models.IntegerField(null=True, blank=True)
    substat_4 = models.IntegerField(choices=STAT_CHOICES, null=True, blank=True)
    substat_4_value = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.TYPE_CHOICES[self.type - 1][1] + ', Slot ' + str(self.slot) + ', ' + str(self.stars) + '*, Lvl ' + str(self.level) + ', +' + str(self.main_stat_value) + ' ' + self.STAT_CHOICES[self.main_stat - 1][1]


class TeamGroup(models.Model):
    owner = models.ForeignKey(Summoner)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(TeamGroup)
    name = models.CharField(max_length=30)
    favorite = models.BooleanField(default=False, blank=True)
    description = models.TextField(null=True, blank=True)
    leader = models.ForeignKey('MonsterInstance', related_name='team_leader', null=True, blank=True)
    roster = models.ManyToManyField('MonsterInstance', blank=True)

    class Meta:
        ordering = ['name']

    def owner(self):
        return self.group.owner

    def __unicode__(self):
        return self.name

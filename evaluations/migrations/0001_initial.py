# Generated by Django 5.2.1 on 2025-05-18 05:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academic', '0001_initial'),
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Examen',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('numero_parcial', models.IntegerField()),
                ('titulo', models.CharField(max_length=100)),
                ('descripcion', models.CharField(blank=True, max_length=100)),
                ('fecha_examen', models.DateField()),
                ('ponderacion', models.DecimalField(decimal_places=2, max_digits=5)),
                ('profesor_materia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.profesormateria')),
                ('trimestre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.trimestre')),
            ],
            options={
                'db_table': 'examenes',
            },
        ),
        migrations.CreateModel(
            name='HistoricoAnual',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('promedio_anual', models.DecimalField(decimal_places=2, max_digits=5)),
                ('promedio_t1', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('promedio_t2', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('promedio_t3', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('porcentaje_asistencia_anual', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('total_participaciones', models.IntegerField(default=0)),
                ('estado_materia', models.CharField(choices=[('aprobado', 'Aprobado'), ('reprobado', 'Reprobado'), ('en_recuperacion', 'En Recuperación')], max_length=20)),
                ('observaciones', models.CharField(blank=True, max_length=50)),
                ('fecha_calculo', models.DateTimeField(auto_now_add=True)),
                ('alumno', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.alumno')),
                ('gestion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.gestion')),
                ('materia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.materia')),
            ],
            options={
                'db_table': 'historico_anual',
            },
        ),
        migrations.CreateModel(
            name='HistoricoTrimestral',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('promedio_trimestre', models.DecimalField(decimal_places=2, max_digits=5)),
                ('promedio_examenes', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('promedio_tareas', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('porcentaje_asistencia', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('num_participaciones', models.IntegerField(default=0)),
                ('observaciones', models.CharField(blank=True, max_length=50)),
                ('fecha_calculo', models.DateTimeField(auto_now_add=True)),
                ('alumno', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.alumno')),
                ('materia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.materia')),
                ('trimestre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.trimestre')),
            ],
            options={
                'db_table': 'historico_trimestral',
            },
        ),
        migrations.CreateModel(
            name='NotaExamen',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nota', models.DecimalField(decimal_places=2, max_digits=5)),
                ('observaciones', models.CharField(blank=True, max_length=100)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('examen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='evaluations.examen')),
                ('matriculacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.matriculacion')),
            ],
            options={
                'db_table': 'notas_examenes',
            },
        ),
        migrations.CreateModel(
            name='Participacion',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('fecha', models.DateField()),
                ('descripcion', models.CharField(max_length=50)),
                ('valor', models.IntegerField()),
                ('horario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.horario')),
                ('matriculacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.matriculacion')),
            ],
            options={
                'db_table': 'participaciones',
            },
        ),
        migrations.CreateModel(
            name='Tarea',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('titulo', models.CharField(max_length=50)),
                ('descripcion', models.CharField(blank=True, max_length=50)),
                ('fecha_asignacion', models.DateField()),
                ('fecha_entrega', models.DateField()),
                ('ponderacion', models.DecimalField(decimal_places=2, max_digits=5)),
                ('profesor_materia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.profesormateria')),
                ('trimestre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.trimestre')),
            ],
            options={
                'db_table': 'tareas',
            },
        ),
        migrations.CreateModel(
            name='NotaTarea',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nota', models.DecimalField(decimal_places=2, max_digits=5)),
                ('observaciones', models.CharField(blank=True, max_length=50)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('matriculacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.matriculacion')),
                ('tarea', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='evaluations.tarea')),
            ],
            options={
                'db_table': 'notas_tareas',
            },
        ),
        migrations.CreateModel(
            name='Asistencia',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('fecha', models.DateField()),
                ('estado', models.CharField(choices=[('P', 'Presente'), ('F', 'Falta'), ('T', 'Tardanza'), ('J', 'Justificada')], max_length=1)),
                ('horario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.horario')),
                ('matriculacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.matriculacion')),
            ],
            options={
                'db_table': 'asistencias',
                'unique_together': {('matriculacion', 'horario', 'fecha')},
            },
        ),
        migrations.AddConstraint(
            model_name='examen',
            constraint=models.CheckConstraint(condition=models.Q(('numero_parcial__gte', 1), ('numero_parcial__lte', 3)), name='check_numero_parcial'),
        ),
        migrations.AddConstraint(
            model_name='examen',
            constraint=models.CheckConstraint(condition=models.Q(('ponderacion__gt', 0)), name='check_ponderacion_positiva'),
        ),
        migrations.AlterUniqueTogether(
            name='historicoanual',
            unique_together={('alumno', 'gestion', 'materia')},
        ),
        migrations.AlterUniqueTogether(
            name='historicotrimestral',
            unique_together={('alumno', 'trimestre', 'materia')},
        ),
        migrations.AddConstraint(
            model_name='notaexamen',
            constraint=models.CheckConstraint(condition=models.Q(('nota__gte', 0), ('nota__lte', 100)), name='check_nota_examen_rango'),
        ),
        migrations.AlterUniqueTogether(
            name='notaexamen',
            unique_together={('matriculacion', 'examen')},
        ),
        migrations.AddConstraint(
            model_name='participacion',
            constraint=models.CheckConstraint(condition=models.Q(('valor__gte', 1), ('valor__lte', 5)), name='check_valor_participacion'),
        ),
        migrations.AddConstraint(
            model_name='tarea',
            constraint=models.CheckConstraint(condition=models.Q(('fecha_entrega__gte', models.F('fecha_asignacion'))), name='check_fecha_entrega_valida'),
        ),
        migrations.AddConstraint(
            model_name='tarea',
            constraint=models.CheckConstraint(condition=models.Q(('ponderacion__gt', 0)), name='check_ponderacion_tarea_positiva'),
        ),
        migrations.AddConstraint(
            model_name='notatarea',
            constraint=models.CheckConstraint(condition=models.Q(('nota__gte', 0), ('nota__lte', 100)), name='check_nota_tarea_rango'),
        ),
        migrations.AlterUniqueTogether(
            name='notatarea',
            unique_together={('matriculacion', 'tarea')},
        ),
    ]

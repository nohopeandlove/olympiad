"""Initial PostgreSQL schema, frozen at revision 0001."""
from alembic import op
revision="0001"
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    op.execute('\nCREATE TABLE olympiads (\n\tid VARCHAR(36) NOT NULL, \n\ttype VARCHAR(30) NOT NULL, \n\ttitle VARCHAR(200) NOT NULL, \n\tdescription TEXT NOT NULL, \n\trules TEXT NOT NULL, \n\tstatus VARCHAR NOT NULL, \n\tregistration_start TIMESTAMP WITH TIME ZONE NOT NULL, \n\tregistration_end TIMESTAMP WITH TIME ZONE NOT NULL, \n\tallowed_classes JSON NOT NULL, \n\tranking_visible BOOLEAN NOT NULL, \n\tPRIMARY KEY (id)\n)\n\n')
    op.execute('\nCREATE TABLE users (\n\tid VARCHAR(36) NOT NULL, \n\temail VARCHAR(254) NOT NULL, \n\tpassword_hash TEXT NOT NULL, \n\trole VARCHAR NOT NULL, \n\tlast_name VARCHAR(100) NOT NULL, \n\tfirst_name VARCHAR(100) NOT NULL, \n\tmiddle_name VARCHAR(100) NOT NULL, \n\tbirth_date DATE NOT NULL, \n\tphone VARCHAR(30) NOT NULL, \n\tregion VARCHAR(150) NOT NULL, \n\tcity VARCHAR(150) NOT NULL, \n\torganization VARCHAR(300) NOT NULL, \n\tverified BOOLEAN NOT NULL, \n\tblocked BOOLEAN NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (email)\n)\n\n')
    op.execute('\nCREATE TABLE audit_logs (\n\tid VARCHAR(36) NOT NULL, \n\tactor_id VARCHAR(36) NOT NULL, \n\taction VARCHAR(100) NOT NULL, \n\ttarget_id VARCHAR(36) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(actor_id) REFERENCES users (id)\n)\n\n')
    op.execute('\nCREATE TABLE email_verifications (\n\tid VARCHAR(64) NOT NULL, \n\tuser_id VARCHAR(36) NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n')
    op.execute('\nCREATE TABLE notifications (\n\tid VARCHAR(36) NOT NULL, \n\tuser_id VARCHAR(36) NOT NULL, \n\tmessage TEXT NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n')
    op.execute('\nCREATE TABLE olympiad_registrations (\n\tid VARCHAR(36) NOT NULL, \n\tuser_id VARCHAR(36) NOT NULL, \n\tolympiad_id VARCHAR(36) NOT NULL, \n\tschool_class INTEGER, \n\tcourse INTEGER, \n\t"group" VARCHAR(100) NOT NULL, \n\tstatus VARCHAR NOT NULL, \n\tconsent_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (user_id, olympiad_id), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tFOREIGN KEY(olympiad_id) REFERENCES olympiads (id)\n)\n\n')
    op.execute('\nCREATE TABLE sessions (\n\tid VARCHAR(64) NOT NULL, \n\tuser_id VARCHAR(36) NOT NULL, \n\tcsrf VARCHAR(64) NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n')
    op.execute('\nCREATE TABLE stages (\n\tid VARCHAR(36) NOT NULL, \n\tolympiad_id VARCHAR(36) NOT NULL, \n\ttitle VARCHAR(150) NOT NULL, \n\tkind VARCHAR NOT NULL, \n\tstarts_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tends_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tduration_minutes INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(olympiad_id) REFERENCES olympiads (id)\n)\n\n')
    op.execute('\nCREATE TABLE anti_cheat_events (\n\tid VARCHAR(36) NOT NULL, \n\tparticipant_id VARCHAR(36) NOT NULL, \n\tolympiad_id VARCHAR(36) NOT NULL, \n\tstage_id VARCHAR(36) NOT NULL, \n\tevent_type VARCHAR(50) NOT NULL, \n\ttimestamp TIMESTAMP WITH TIME ZONE NOT NULL, \n\tmetadata JSON NOT NULL, \n\tseverity VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(participant_id) REFERENCES olympiad_registrations (id), \n\tFOREIGN KEY(olympiad_id) REFERENCES olympiads (id), \n\tFOREIGN KEY(stage_id) REFERENCES stages (id)\n)\n\n')
    op.execute('\nCREATE TABLE participants (\n\tid VARCHAR(36) NOT NULL, \n\tregistration_id VARCHAR(36) NOT NULL, \n\tstage_id VARCHAR(36) NOT NULL, \n\tstarted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tdeadline TIMESTAMP WITH TIME ZONE NOT NULL, \n\tsession_hash VARCHAR(64) NOT NULL, \n\tfinished BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (registration_id, stage_id), \n\tFOREIGN KEY(registration_id) REFERENCES olympiad_registrations (id), \n\tFOREIGN KEY(stage_id) REFERENCES stages (id)\n)\n\n')
    op.execute('\nCREATE TABLE tasks (\n\tid VARCHAR(36) NOT NULL, \n\tolympiad_id VARCHAR(36) NOT NULL, \n\tstage_id VARCHAR(36) NOT NULL, \n\ttitle VARCHAR(200) NOT NULL, \n\tstatement TEXT NOT NULL, \n\tinput_description TEXT NOT NULL, \n\toutput_description TEXT NOT NULL, \n\tconstraints TEXT NOT NULL, \n\tdifficulty VARCHAR NOT NULL, \n\ttime_limit INTEGER NOT NULL, \n\tmemory_limit INTEGER NOT NULL, \n\tpoints INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(olympiad_id) REFERENCES olympiads (id), \n\tFOREIGN KEY(stage_id) REFERENCES stages (id)\n)\n\n')
    op.execute('\nCREATE TABLE drafts (\n\tid VARCHAR(36) NOT NULL, \n\tuser_id VARCHAR(36) NOT NULL, \n\ttask_id VARCHAR(36) NOT NULL, \n\tcode TEXT NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (user_id, task_id), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tFOREIGN KEY(task_id) REFERENCES tasks (id)\n)\n\n')
    op.execute('\nCREATE TABLE submissions (\n\tid VARCHAR(36) NOT NULL, \n\tuser_id VARCHAR(36) NOT NULL, \n\tolympiad_id VARCHAR(36) NOT NULL, \n\tstage_id VARCHAR(36) NOT NULL, \n\ttask_id VARCHAR(36) NOT NULL, \n\tcode TEXT NOT NULL, \n\tmode VARCHAR NOT NULL, \n\tstatus VARCHAR NOT NULL, \n\tscore INTEGER NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tFOREIGN KEY(olympiad_id) REFERENCES olympiads (id), \n\tFOREIGN KEY(stage_id) REFERENCES stages (id), \n\tFOREIGN KEY(task_id) REFERENCES tasks (id)\n)\n\n')
    op.execute('\nCREATE TABLE test_cases (\n\tid VARCHAR(36) NOT NULL, \n\ttask_id VARCHAR(36) NOT NULL, \n\tinput TEXT NOT NULL, \n\texpected TEXT NOT NULL, \n\tpublic BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(task_id) REFERENCES tasks (id)\n)\n\n')
    op.execute('\nCREATE TABLE submission_results (\n\tid VARCHAR(36) NOT NULL, \n\tsubmission_id VARCHAR(36) NOT NULL, \n\tdetail JSON NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (submission_id), \n\tFOREIGN KEY(submission_id) REFERENCES submissions (id)\n)\n\n')

def downgrade():
    op.drop_table('submission_results')
    op.drop_table('test_cases')
    op.drop_table('submissions')
    op.drop_table('drafts')
    op.drop_table('tasks')
    op.drop_table('participants')
    op.drop_table('anti_cheat_events')
    op.drop_table('stages')
    op.drop_table('sessions')
    op.drop_table('olympiad_registrations')
    op.drop_table('notifications')
    op.drop_table('email_verifications')
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('olympiads')

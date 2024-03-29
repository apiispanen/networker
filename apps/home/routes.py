# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from apps.home import blueprint
from flask import render_template, request, session
from flask_login import login_required
from jinja2 import TemplateNotFound
from bson.objectid import ObjectId
from datetime import datetime


@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:
        if not template.endswith('.html'):
            pass
            # template = template+('.html')

        # Detect the current page
        segment = get_segment(request)
        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None





# DREW NETWORKER

print("************************************ RUNNING ROUTES FILE ************************************")

import os
# from stt import speech_to_text
from apps.home.prompt import ai_response
from apps.home.tts import tts_string, azure_speak_string
from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
from flask import session
from apps.home.database import get_people, log_user_response, client, update_person, delete_object, remove_field, get_notes, add_person, edit_name
from apps.home.user import Session, person
from html import escape

networker = Session()

app = Flask(__name__)
app.config["CACHE_TYPE"] = "null"

# @app.route('/')
# def index():
#     session['respond'] = True
#     return render_template('voice.html')

# OBJECT ID IS DESIGNATED
object_id = "63fd0087b9b2b4001ccb7c5f"

@blueprint.route('/people')
def people():
    object_id = "63fd0087b9b2b4001ccb7c5f"
    
    qTerm = request.args.get('s')
    if not qTerm:    
        print("NO Qterm")
        data = get_people(object_id=object_id)     
        qTerm = None   
        # flash("You did not search for anything")
        # return redirect(url_for('home_blueprint.people'))
    elif qTerm:
        print("Qy")
        qTerm = escape(qTerm)
        print(qTerm)
        data = get_people(object_id=object_id, search_term=qTerm)

    it = iter(data['People']).__next__


    return render_template('home/people.html', data=data, it=it, object_id=object_id, qTerm=qTerm, segment=get_segment(request))

@blueprint.route('/people2')
def people2():
    data = get_people()
    it = iter(data['People']).__next__
    # qTerm = request.args.get('s')
    # if not qTerm:    
    #     flash("You did not search for anything")
    #     return redirect(url_for('home_blueprint.people'))
    # elif qTerm:
    #     cleanQuery = escape(qTerm)

    return render_template('home/people2.html', data=data, it=it, segment=get_segment(request))

# @blueprint.route('/demo')
# def demo():
#     return render_template('home/voice.html')

# RETURNS RESPONSE
@blueprint.route("/ask_question", methods=['POST'])
@login_required
def ask_question():
    print("SOMETHING HAPPENING HERE")
    # process the audio data here
    
    # mark the function as called
    session['audio_saved'] = True
    
    # read the audio data from the request body
    prompt = request.json['words']
    networking = request.json['networking'] 
    print("RAW PROMPT FROM JS: ",prompt)
    # IF THERE'S MORE THAN 1 WORD, PROCESS THE REQUEST:

    if len(prompt.split(' ')) > 1:
        print("YOUR PROMPT:", prompt.split(' '),  len(prompt))
        response = ai_response(prompt, networking=networking)
        user_id = session.get("_user_id")
        log_user_response(user_id, prompt, response, type="prompt", client=client)
        print("AI response Completed.")
    # ELSE, REDIRECT
    else:
        response = "How can I help you?"

    # audioContent = tts_string(response)
    # do something with the audio data here
    return jsonify({ "airesponse":response})

# RETURNS JSON FILE WITH AUDIO STRING
@blueprint.route('/speak', methods=['POST', 'GET'])
def speak_route():
    words = request.json['body']
    # Call the speak() function and get the audio file URL and text result
    while True:
        print("sending to azure")
        audio_content, text_result = azure_speak_string(words)
        # Return the audio URL and text result as a JSON object
        return jsonify({
            'audioContent': audio_content,
            'textResult': text_result
        })
    

@blueprint.route("/prompts")
@login_required
def prompts():
    print("PROMPTS")
    # Connect to MongoDB and query for unique prompts
    db = client["db"]
    collection = db["user_responses"]
    # user_id = 'user123'
    user_id = session.get("_user_id")

    prompts = collection.find({"user": user_id})
 
    qTerm = request.args.get('s')
    if not qTerm:    
        prompts = collection.find({"user": user_id, 'type':'prompt'})
        flash("You did not search for anything")
        res="ALL"
        # return redirect(url_for('home_blueprint.prompts'))
    elif qTerm:
        cleanQuery = escape(qTerm)
        # Do a search on the user and the query, case insensitive "i" option
        prompts = collection.find({"user": user_id,'type':'prompt', '$or':[
                                    {"prompt":{'$regex':cleanQuery, '$options' : 'i'}},
                                    { "response":{'$regex':cleanQuery, '$options' : 'i'}}
                                   ]                        })
        
        res = 'assume it has been searched'
    
    prompts = prompts.sort("timestamp", -1)
    return render_template('home/prompts.html', prompts=prompts, user_id=user_id, res=res, segment=get_segment(request))

from flask_paginate import Pagination, get_page_parameter

@blueprint.route("/notes")
@login_required
def notes():
    # Connect to MongoDB and query for unique prompts
    user_id = session.get("_user_id")
    # notes = collection.find({"user": user_id})
    qTerm = request.args.get('s')
    notes = get_notes(user_id, qTerm)
    # print(notes)
    # Pagination logic
    # page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 5 # Change this to however many notes you want to display per page
    # offset = (1 - 1) * per_page
    # notes_count = len(list(notes))
    notes = notes[:per_page]
    # pagination = Pagination(page=page, total=notes_count, per_page=per_page, css_framework='bootstrap4')
    print("NOTES", list(notes))
    length = len([note for note in list(notes)])
    print(f"Length: {length}")
    return render_template('home/notes.html', noteprompts= notes, length = length, user_id=user_id, qTerm=qTerm, segment=get_segment(request))


@blueprint.route("/verify_person", methods=['POST'])
@login_required
def verify_person():
    data = request.get_json()
    entity_value = data.get('entityValue')
    # print(f"looking for '{entity_value}'")
    entry = person(name = entity_value)
    entry.verify()
    return jsonify(entry.name)

@blueprint.route("/relevant_fields", methods=['POST'])
@login_required
def relevant_fields():
    data = request.get_json()
    entity_value = data.get('entityValue')
    # entry = person(name = entity_value)
    # result = entry.verify()
    return 

@blueprint.route('/up-person', methods=['POST'])
def up_person():
    name = request.form['name'].strip()
    namechange = request.form['namechange'].strip()
    value = request.form['value'].strip()
    if namechange == "true":
        print(f':NAME CHANGE, Name:{name} Value:{value}')
        edit_name(name, value)
        return jsonify(success=True)
    oldvalue = request.form['oldvalue'].strip()
    # field = request.form['field']
    # Format the value into an actual dict, ugh:
    parts = value.split(':')
    key = parts[0].strip()
    if(key != oldvalue):
        print(f"key: {key}, oldvalue:{oldvalue}")
        remove_field(oldvalue, name)
    try:
        value = parts[1].strip()
        value = {key: value}
    except:
        print(f"REMOVING FIELD: {oldvalue}, value: {value}")
        value = ''
    
    # print(key, value)
    update_person(name, value, oldvalue )
    # ({"People": {"$exists": True}}, {"$set": {"People."+name+"."+str(key): str(json_input[key])}})
    return jsonify(success=True)

@blueprint.route("/new_note", methods=['POST'])
@login_required
def new_note():
    data = request.get_json()
    # NOW GET THE DATA FROM TEXTAREAS #FORM2 and #FORM3
    form3_data = data.get('note')
    form2_data = data.get('person')
    
    # Process the data here...
    
    # Return a JSON response with the processed data
    response_data = {
        'success': True,
        'message': 'Note submitted successfully!',
        'processed_data': {
            'note': form3_data,
            'person': form2_data
        }
    }
    print(f"NOTE: {response_data['processed_data']['note']}")
    print(f"PERSON: {response_data['processed_data']['person']}")

    user_id = session.get("_user_id")
    log_user_response(user_id, response_data['processed_data']['note'], person_of_interest=response_data['processed_data']['person'], type="note")
    return jsonify(response_data)

@blueprint.route("/new_person", methods=['POST'])
@login_required
def new_person():
    data = request.get_json()
    # NOW GET THE DATA FROM TEXTAREAS #FORM2 and #FORM3
    form3_data = data.get('note')
    form2_data = data.get('person')
    # Process the data here...
    # Return a JSON response with the processed data
    response_data = {
        'success': True,
        'message': 'Note submitted successfully!',
        'processed_data': {
            'note': form3_data,
            'person': form2_data
        }
    }
    print(f"NOTE: {response_data['processed_data']['note']}")
    print(f"PERSON: {response_data['processed_data']['person']}")
    user_id = session.get("_user_id")
    add_person(response_data['processed_data']['person'], dict(response_data['processed_data']['note']), client=client)
    return jsonify(response_data)

@blueprint.route('/repurpose',methods=['POST'])
def repurpose():
    data = request.get_json()
    text = data.get('text')
    
    # NEED TO AI REPURPOSE SCRIPT
    prompt = f"Please repurpose and properly format the following note: {text}"
    new_text = ai_response(prompt, networking=False)

    # Return a JSON response with the processed data
    response_data = {
        'success': True,
            'text': new_text
    }
    return jsonify(response_data)


@blueprint.route('/delete/<collection>/<objectID>', methods=['GET','POST'])
@login_required
def delete(collection,objectID):
    print(f"INCOMING POST AT DELETE/{collection}/{objectID}")
    delete_object(collection,objectID)
    # Return a JSON response with the processed data
    response_data = {
        'success': True,
            'text': 'deleted'
    }
    return jsonify(response_data)


@blueprint.route('/remove-field/<objectID>/<person_name>/<field_name>', methods=['GET','POST'])
@login_required
def delete_field(objectID, person_name,field_name):
    # print(f"INCOMING FIELD DELETION AT DELETE/{field_name}/{person_name}/{field_name}")
    remove_field(field_name, person_name, objectID)

    # Return a JSON response with the processed data
    response_data = {
        'success': True,
            'text': 'deleted'
    }
    return jsonify(response_data)

from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from bson import ObjectId


class EditForm(FlaskForm):
    user = StringField('User', validators=[DataRequired()])
    prompt = StringField('Prompt', validators=[DataRequired()])
    response = StringField('Response', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired()])
    person = StringField('Person')
    submit = SubmitField('Update')

@blueprint.route('/edit/<object_id>', methods=['GET', 'POST'])
@login_required
def edit(object_id):
    # Get the document by its _id field
    collection = client['db']['user_responses']
    document = collection.find_one({'_id': ObjectId(object_id)})
    print(document)
    # Create an instance of the EditForm and prepopulate the fields with the document data
    form = EditForm(obj=document)
    if form.validate_on_submit():
        # Update the document with the new form data
        collection.update_one({'_id': ObjectId(object_id)}, {'$set': {'user': form.user.data, 'prompt': form.prompt.data, 'response': form.response.data, 'type': form.type.data, 'timestamp': datetime.utcnow(), 'person': form.person.data}})
        flash('Response updated successfully!', 'success')
    return render_template('cards/edit.html', form=form, document=document)



if __name__ == '__main__':
    app.run()
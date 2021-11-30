import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from sqlalchemy.sql.expression import select
from werkzeug.exceptions import InternalServerError

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


# paginate_helper_function

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers",
            "Content-Type,Authorization,true")
        response.headers.add(
            "Access-Control-Allow-Methods",
            "GET,PUT,POST,DELETE,OPTIONS")
        return response

    @app.route("/categories")
    def get_categories():
        try:
            categories = Category.query.order_by(Category.id).all()

            return jsonify({
                'success': True,
                'categories': {
                    category.id: category.type for category in categories
                }
            })
        except Exception:
            abort(422)

    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.all()
        paginated_questions = paginate_questions(request, selection)
        if len(paginated_questions) == 0:
            abort(404)
        categories = Category.query.order_by(Category.id).all()
        categories_formatted = {
            category.id: category.type for category in categories
        }

        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(selection),
            'categories': categories_formatted
        })

    @app.route("/questions/<int:question_id>", methods=['DELETE'])
    def delete_questions(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)
            question.delete()
            questions = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions)
            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": current_questions,
                    "total_questions": len(current_questions)
                }
            )
        except Exception as e:
            if '404' in str(e):
                abort(404)
            else:
                abort(422)

    @app.route("/questions", methods=["POST"])
    def add_questions():
        body = request.get_json()
        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_difficulty = body.get("difficulty", None)
        new_category = body.get("category", None)

        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty)
            question.insert()
            return jsonify({
                "success": True,
                "created": question.id,
            })
        except Exception:
            abort(422)

    @app.route('/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        search = body.get('searchTerm', None)

        try:
            selection = Question.query.order_by(Question.id). \
                filter(Question.question.ilike("%{}%".format(search))
                       ).all()
            current_questions = paginate_questions(request, selection)
            total_questions = len(current_questions)
            return jsonify({
                "success": True,
                "questions": current_questions,
                "total_questions": total_questions,
                "current_category": None
            })
        except:
            abort(422)

    @app.route("/categories/<int:category_id>/questions")
    def get_questions_under_same_category(category_id):
        selection = Question.query.filter(Question.category == category_id).all()

        try:
            current_questions = paginate_questions(request, selection)
            if len(current_questions) == 0:
                abort(404)
            return jsonify({
                "success": True,
                "questions": current_questions
            })
        except Exception as e:
            if '404' in str(e):
                abort(404)
            else:
                abort(422)

    @app.route("/quizzes", methods=["POST"])
    def play_quizzes():
        try:
            questions = None
            body = request.get_json()
            quiz_category = body.get("quiz_category", None)
            previous_questions = body.get("previous_questions", None)
            category_id = quiz_category.get("id")

            if category_id == 0:
                questions = Question.query.all()

            else:
                questions = Question.query \
                    .filter(Question.category == category_id) \
                    .all()
            questions_formatted = [question.format() for question in questions]
            all_ids = [q.get("id") for q in questions_formatted]
            found_one = False

            for i in all_ids:
                if i not in previous_questions:
                    found_one = True
                    next_question_id = i
                    break

            if not found_one:
                return jsonify({
                    'success': True,
                    'question': None
                })
            else:
                question = Question.query.get(next_question_id)

                return jsonify({
                    'success': True,
                    'question': question.format()
                })

        except Exception:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return (jsonify({"success": False, "error": 404,
                         "message": "resource not found"}), 404,)

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False, "error": 400, "message": "bad request"
        }), 400

    @app.errorhandler(405)
    def not_found(error):
        return (jsonify({"success": False, "error": 405,
                         "message": "method not allowed"}), 405,)

    return app

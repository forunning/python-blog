#  encoding: utf-8

from flask import Flask,render_template,request,redirect,url_for,session,g
import config
from models import User,Question,Answer
from exts import db
from decorators import login_required

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Question.query.paginate(page, per_page=10, error_out=False)
    pagination1 =Answer.query.order_by(db.desc(Answer.create_time)).limit(5)
    pagination2=Question.query.order_by(db.desc(Question.create_time)).limit(5)
    context ={
        'questions':pagination.items,
        'answers':pagination1,
        'question_show':pagination2
    }

    return render_template('index.html', pagination=pagination, **context)


@app.route('/login/',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter(User.username == username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return u'用户名或者密码错误，请确认后再登录！'


@app.route('/regist/',methods=['GET','POST'])
def regist():
    if request.method == 'GET':
        return render_template('regist.html')
    else:
        telephone = request.form.get('telephone')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # 用户名验证，如果被注册了，就不能再注册了
        user = User.query.filter(User.username == username).first()
        if user:
            return u'该用户名已被注册，请重新注册！'
        else:
            # password1要和password2相等才可以
            if password1 != password2:
                return u'两次密码不相等，请核对后再填写！'
            else:
                user = User(telephone=telephone,username=username,password=password1)
                db.session.add(user)
                db.session.commit()
                # 如果注册成功，就让页面跳转到登录的页面
                return redirect(url_for('login'))


@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/question/',methods=['GET','POST'])
@login_required
def question():
    if request.method == 'GET':
        question_id = request.args.get('id', -1, type=int)
        if question_id == -1:
            return render_template('question.html',id=question_id)
        else:
            question = Question.query.filter(Question.id == question_id).first()
            return render_template('question.html', id=question_id, question=question)
    else:
        name = request.form.get('todo')
        if name == 'add':
            title = request.form.get('title')
            content = request.form.get('content')
            question = Question(title=title,content=content)
            question.author = g.user
            db.session.add(question)
            db.session.commit()
            return redirect(url_for('index'))
        elif name == 'update':
            question_id = request.form.get('question_id')
            print question_id
            question = Question.query.filter(Question.id == question_id).first()
            question.title = request.form.get('title')
            question.content = request.form.get('content')
            db.session.commit()
            return redirect(url_for('index'))


@app.route('/question_del/',methods=['GET','POST'])
@login_required
def question_del():
    question_id = request.args.get('id', -1, type=int)
    if question_id != -1:
        question = Question.query.filter(Question.id == question_id).first()
        answers =Answer.query.filter(Answer.question_id==question_id)
        for answer in answers:
            db.session.delete(answer)
        db.session.delete(question)
        db.session.commit()
        return redirect(url_for('index'))


@app.route('/detail/<question_id>/')
def detail(question_id):
    page = request.args.get('page', 1, type=int)
    pagination = Question.query.paginate(page, per_page=10, error_out=False)
    pagination1 = Answer.query.order_by(db.desc(Answer.create_time)).limit(5)
    pagination2 = Question.query.order_by(db.desc(Question.create_time)).limit(5)
    context = {
        'questions': pagination.items,
        'answers': pagination1,
        'question_show': pagination2
    }
    question_model = Question.query.filter(Question.id == question_id).first()
    return render_template('detail.html',question=question_model,**context)


@app.route('/add_answer/',methods=['POST'])
@login_required
def add_answer():
    content = request.form.get('answer_content')
    question_id = request.form.get('question_id')

    answer = Answer(content=content)
    answer.author = g.user
    question = Question.query.filter(Question.id == question_id).first()
    answer.question = question
    db.session.add(answer)
    db.session.commit()
    return redirect(url_for('detail',question_id=question_id))


@app.route('/del_anwser/',methods=['POST'])
@login_required
def del_answer():
    answer = Answer(id=request.form.get('answer_id'))
    answer_model = Answer.query.filter(Answer.id == answer.id).first()
    question_id = request.form.get('question_id')

    db.session.delete(answer_model)
    db.session.commit()
    return redirect(url_for('detail',question_id=question_id))


@app.route('/search/')
def search():
    q = request.args.get('q')
    questions = Question.query.filter(Question.title.contains(q),Question.content.contains(q))
    return render_template('index.html',questions=questions)


@app.before_request
def my_before_request():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.filter(User.id == user_id).first()
        if user:
            g.user = user

@app.context_processor
def my_context_processor():
    if hasattr(g,'user'):
        return {'user':g.user}
    return {}

# before_request -> 视图函数 -> context_processor

if __name__ == '__main__':
    app.run()

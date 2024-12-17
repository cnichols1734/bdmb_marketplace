from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

app = Flask(__name__,
           template_folder='../templates',
           static_folder='../static')  # Add this line to set static folder

# Configuration
base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "instance", "showcase.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Create upload folder path
upload_folder = os.path.join(base_dir, 'static', 'showcase_uploads')
app.config['UPLOAD_FOLDER'] = upload_folder

# Ensure directories exist
os.makedirs(upload_folder, exist_ok=True)
os.makedirs(os.path.join(base_dir, 'instance'), exist_ok=True)

db = SQLAlchemy(app)

def save_showcase_photo(photo, filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(file_path)
        print(f"Photo saved successfully to: {file_path}")
        return True
    except Exception as e:
        print(f"Error saving photo: {str(e)}")
        return False

# Models
class ShowcasePost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    craftsman_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.String(200))
    photos = db.relationship('ShowcasePhoto', backref='showcase_post', lazy=True, cascade='all, delete')
    comments = db.relationship('ShowcaseComment', backref='showcase_post', lazy=True, cascade='all, delete')
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    website = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_password = db.Column(db.String(255))
    likes = db.Column(db.Integer, default=0)


class ShowcasePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    caption = db.Column(db.String(200))
    post_id = db.Column(db.Integer, db.ForeignKey('showcase_post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class ShowcaseComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100))
    post_id = db.Column(db.Integer, db.ForeignKey('showcase_post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Constants
SHOWCASE_CATEGORIES = [
    'Woodworking',
    'Gunsmithing',
    'Metalworking',
    'Leather Crafting',
    'Custom Builds',
    'Other'
]

# Create all tables
with app.app_context():
    db.create_all()


# Routes
@app.route('/')
def showcase_index():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    tag = request.args.get('tag', '')

    query = ShowcasePost.query

    if category:
        query = query.filter(ShowcasePost.category == category)
    if tag:
        query = query.filter(ShowcasePost.tags.like(f'%{tag}%'))

    posts = query.order_by(ShowcasePost.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)

    return render_template('showcase/index.html',
                           posts=posts,
                           categories=SHOWCASE_CATEGORIES,
                           selected_category=category,
                           selected_tag=tag)


@app.route('/create', methods=['GET', 'POST'])
def create_showcase():
    if request.method == 'POST':
        try:
            title = request.form['title']
            description = request.form['description']
            craftsman_name = request.form['craftsman_name']
            category = request.form['category']
            tags = request.form.get('tags', '').strip()
            contact_email = request.form.get('contact_email', '').strip() or None
            contact_phone = request.form.get('contact_phone', '').strip() or None
            website = request.form.get('website', '').strip() or None
            post_password = request.form.get('post_password', '').strip() or None

            new_post = ShowcasePost(
                title=title,
                description=description,
                craftsman_name=craftsman_name,
                category=category,
                tags=tags,
                contact_email=contact_email,
                contact_phone=contact_phone,
                website=website,
                post_password=post_password
            )

            db.session.add(new_post)
            db.session.flush()

            # Handle photo uploads with debugging
            photos_saved = False
            for idx in range(1, 11):
                photo = request.files.get(f'photo{idx}')
                caption = request.form.get(f'caption{idx}', '').strip()

                if photo and photo.filename:
                    filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}")
                    print(f"Processing photo {idx}: {filename}")

                    if save_showcase_photo(photo, filename):
                        new_photo = ShowcasePhoto(
                            filename=filename,
                            caption=caption,
                            post_id=new_post.id
                        )
                        db.session.add(new_photo)
                        photos_saved = True
                        print(f"Photo {idx} added to database")

            if not photos_saved:
                print("No photos were processed")

            db.session.commit()
            print(f"Showcase post created successfully with ID: {new_post.id}")
            return redirect(url_for('showcase_post', post_id=new_post.id))

        except Exception as e:
            print(f"Error creating showcase post: {str(e)}")
            db.session.rollback()
            flash('An error occurred while creating your showcase post.', 'error')
            return redirect(url_for('create_showcase'))

    return render_template('showcase/create.html', categories=SHOWCASE_CATEGORIES)


@app.route('/post/<int:post_id>')
def showcase_post(post_id):
    post = ShowcasePost.query.get_or_404(post_id)
    return render_template('showcase/post.html', post=post)


@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    post = ShowcasePost.query.get_or_404(post_id)

    content = request.form.get('content')
    author_name = request.form.get('author_name', 'Anonymous')

    if content:
        comment = ShowcaseComment(
            content=content,
            author_name=author_name,
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')

    return redirect(url_for('showcase_post', post_id=post_id))


@app.route('/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    post = ShowcasePost.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    return {'likes': post.likes}


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_showcase(post_id):
    post = ShowcasePost.query.get_or_404(post_id)

    if request.method == 'POST':
        input_password = request.form.get('post_password', '').strip()

        if post.post_password is None:
            flash('This post has no password set and cannot be edited.', 'error')
            return redirect(url_for('showcase_post', post_id=post.id))

        if input_password != post.post_password:
            flash('Incorrect password. You are not authorized to edit this post.', 'error')
            return render_template('showcase/edit.html', post=post, categories=SHOWCASE_CATEGORIES)

        try:
            # Update post with new fields
            post.title = request.form['title']
            post.description = request.form['description']
            post.craftsman_name = request.form['craftsman_name']
            post.category = request.form['category']
            post.tags = request.form.get('tags', '').strip()
            post.contact_email = request.form.get('contact_email', '').strip() or None
            post.contact_phone = request.form.get('contact_phone', '').strip() or None
            post.website = request.form.get('website', '').strip() or None

            # Handle new photos if any
            for idx in range(1, 11):
                photo = request.files.get(f'photo{idx}')
                caption = request.form.get(f'caption{idx}', '').strip()

                if photo and photo.filename:
                    filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}")
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    new_photo = ShowcasePhoto(
                        filename=filename,
                        caption=caption,
                        post_id=post.id
                    )
                    db.session.add(new_photo)

            db.session.commit()
            flash('Post updated successfully.', 'success')
            return redirect(url_for('showcase_post', post_id=post.id))

        except Exception as e:
            print(f"Error updating showcase post: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the post.', 'error')
            return redirect(url_for('showcase_post', post_id=post.id))

    return render_template('showcase/edit.html', post=post, categories=SHOWCASE_CATEGORIES)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_showcase(post_id):
    try:
        post = ShowcasePost.query.get_or_404(post_id)
        input_password = request.form.get('post_password', '').strip()

        if post.post_password:
            if input_password != post.post_password:
                flash('Incorrect password. You are not authorized to delete this post.', 'error')
                return redirect(url_for('showcase_post', post_id=post.id))
        else:
            flash('No password set, unable to verify ownership. Cannot delete.', 'error')
            return redirect(url_for('showcase_post', post_id=post.id))

        # Delete associated photos from filesystem
        for photo in post.photos:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)

        db.session.delete(post)
        db.session.commit()
        flash('Your post has been deleted.', 'success')
        return redirect(url_for('showcase_index'))

    except Exception as e:
        print(f"Error deleting showcase post: {str(e)}")
        db.session.rollback()
        flash('An error occurred while deleting the post.', 'error')
        return redirect(url_for('showcase_post', post_id=post_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5008)
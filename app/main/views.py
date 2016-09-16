# -*-coding: utf-8-*-
import os
from datetime import datetime
from flask import render_template, session, redirect, \
    url_for, flash, abort, request, current_app
from flask_login import login_required, current_user
from werkzeug import secure_filename


from . import main
from .forms import TagForm, WallForm, NormalForm, EditProfileForm, EditProfileAdminForm, TESTForm
from .. import db
from ..models import User, Role, Permission, Album, Photo
from tag import glue
from ..decorators import admin_required, permission_required



@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    albums = user.albums.order_by(Album.timestamp.desc()).all()
    return render_template('user.html', user=user, albums=albums)


@main.route('/user/<username>/albums')
def albums(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    albums = user.albums.order_by(Album.timestamp.desc()).all()
    album_count = len(albums)
    return render_template('albums.html', user=user, albums=albums, album_count=album_count)


@main.route('/album/<int:id>')
def album(id):
    album = Album.query.get_or_404(id)
    photos = album.photos.order_by(Photo.timestamp.asc())
    return render_template('album.html', album=album, photos=photos)


@main.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.website = form.website.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash(u'你的资料已经更新。')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.website.data = current_user.website
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.website = form.website.data
        user.about_me = form.about_me.data
        db.session.add(current_user)
        flash(u'资料已经更新。')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role
    form.name.data = user.name
    form.location.data = user.location
    form.website.data = user.website
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/create-tag', methods=['GET', 'POST'])
def tag():
    flash(u'目前只是测试阶段，仅支持标签云相册，暂不提供永久存储。不好意思>_<')
    form = TagForm()
    app = current_app._get_current_object()
    if form.validate_on_submit():
        title = form.title.data
        sub_title = form.sub_title.data
        theme = form.theme.data
        pro_attachment = request.files.getlist('pro_attachment1')
        for upload in pro_attachment:
            filename = upload.filename.rsplit("/")[0]
            destination = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)
            print "Accept incoming file:", filename
            print "Save it to:", destination
            upload.save(destination)
        # glue()
        return render_template('tag_album.html', title=title, sub_title=sub_title)
    return render_template('create/tag.html', form=form)


@main.route('/create-wall', methods=['GET', 'POST'])
def wall():
    form = WallForm()
    if form.validate_on_submit():
        title = form.title.data
        sub_title = form.sub_title.data
        theme = form.theme.data
        return render_template('wall_album.html', title=title, sub_title=sub_title)
    return render_template('create/wall.html', form=form)


@main.route('/create-normal', methods=['GET', 'POST'])
def normal():
    from flask_uploads import UploadSet, configure_uploads, IMAGES
    app = current_app._get_current_object()
    photos = UploadSet('photos', IMAGES)
    form = NormalForm()
    if form.validate_on_submit(): # current_user.can(Permission.CREATE_ALBUMS) and
        if request.method == 'POST' and 'photo' in request.files:
            filename=[]
            for img in request.files.getlist('photo'):
                photos.save(img)
                url = photos.url(img.filename)
                filename.append(url.replace("%20", "_"))
        title = form.title.data
        about = form.about.data
        author = current_user._get_current_object()
        album = Album(title=title,
        about=about, cover=filename[0],
        author = current_user._get_current_object())
        db.session.add(album)

        for file in filename:
            photo = Photo(path=file, album=album)
            db.session.add(photo)
        db.session.commit()
        return redirect(url_for('.album', id=album.id))
    return render_template('create/normal.html', form=form)


@main.route('/base', methods=['GET','POST'])
def test():
    name = None
    form = TESTForm()

    if form.validate_on_submit():
        name = form.name.data
        session['name'] = form.name.data
        return redirect(url_for('base'))

    return render_template('test.html', form=form)

#filename = photos.save(request.files['photo'])